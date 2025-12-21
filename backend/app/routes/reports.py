"""
Report generation API routes
"""
from fastapi import APIRouter, HTTPException, status, Query
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

from ..database import get_surgeries_collection


router = APIRouter(prefix="/api/reports", tags=["reports"])


@router.get("/summary")
async def get_summary_report() -> Dict[str, Any]:
    """Get overall outcome statistics"""
    collection = await get_surgeries_collection()
    
    # Total surgeries
    total_surgeries = await collection.count_documents({})
    
    # Success rate
    successful_surgeries = await collection.count_documents({"outcomes.success": True})
    success_rate = (successful_surgeries / total_surgeries * 100) if total_surgeries > 0 else 0
    
    # Complications
    surgeries_with_complications = await collection.count_documents({
        "outcomes.complications": {"$exists": True, "$ne": []}
    })
    complication_rate = (surgeries_with_complications / total_surgeries * 100) if total_surgeries > 0 else 0
    
    # Readmissions
    readmissions = await collection.count_documents({"outcomes.readmission_30day": True})
    readmission_rate = (readmissions / total_surgeries * 100) if total_surgeries > 0 else 0
    
    # Mortality
    mortality_count = await collection.count_documents({"outcomes.mortality": True})
    mortality_rate = (mortality_count / total_surgeries * 100) if total_surgeries > 0 else 0
    
    # Average length of stay
    pipeline = [
        {"$match": {"outcomes.length_of_stay_days": {"$exists": True, "$ne": None}}},
        {"$group": {"_id": None, "avg_los": {"$avg": "$outcomes.length_of_stay_days"}}}
    ]
    avg_los_result = await collection.aggregate(pipeline).to_list(length=1)
    avg_length_of_stay = round(avg_los_result[0]["avg_los"], 2) if avg_los_result else 0
    
    # Average patient satisfaction
    pipeline = [
        {"$match": {"outcomes.patient_satisfaction": {"$exists": True, "$ne": None}}},
        {"$group": {"_id": None, "avg_satisfaction": {"$avg": "$outcomes.patient_satisfaction"}}}
    ]
    avg_satisfaction_result = await collection.aggregate(pipeline).to_list(length=1)
    avg_satisfaction = round(avg_satisfaction_result[0]["avg_satisfaction"], 2) if avg_satisfaction_result else 0
    
    return {
        "total_surgeries": total_surgeries,
        "success_rate": round(success_rate, 2),
        "complication_rate": round(complication_rate, 2),
        "readmission_rate": round(readmission_rate, 2),
        "mortality_rate": round(mortality_rate, 2),
        "avg_length_of_stay_days": avg_length_of_stay,
        "avg_patient_satisfaction": avg_satisfaction,
        "generated_at": datetime.utcnow().isoformat()
    }


@router.get("/complications")
async def get_complications_report() -> Dict[str, Any]:
    """Get detailed complication analysis"""
    collection = await get_surgeries_collection()
    
    # Unwind complications array and group by type
    pipeline = [
        {"$match": {"outcomes.complications": {"$exists": True, "$ne": []}}},
        {"$unwind": "$outcomes.complications"},
        {"$group": {
            "_id": "$outcomes.complications.type",
            "count": {"$sum": 1},
            "severity_breakdown": {
                "$push": "$outcomes.complications.severity"
            }
        }},
        {"$sort": {"count": -1}}
    ]
    
    complication_types = await collection.aggregate(pipeline).to_list(length=100)
    
    # Count severity levels
    for comp in complication_types:
        severity_counts = {}
        for severity in comp["severity_breakdown"]:
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
        comp["severity_breakdown"] = severity_counts
    
    return {
        "complications_by_type": complication_types,
        "generated_at": datetime.utcnow().isoformat()
    }


@router.get("/trends")
async def get_trends_report(
    days: int = Query(30, description="Number of days to analyze", ge=1, le=365)
) -> Dict[str, Any]:
    """Get trends over specified time period"""
    collection = await get_surgeries_collection()
    
    start_date = datetime.utcnow() - timedelta(days=days)
    
    # Surgeries by date
    pipeline = [
        {"$match": {"procedure.date": {"$gte": start_date}}},
        {"$group": {
            "_id": {"$dateToString": {"format": "%Y-%m-%d", "date": "$procedure.date"}},
            "count": {"$sum": 1},
            "successful": {"$sum": {"$cond": ["$outcomes.success", 1, 0]}},
            "with_complications": {
                "$sum": {
                    "$cond": [
                        {"$gt": [{"$size": {"$ifNull": ["$outcomes.complications", []]}}, 0]},
                        1,
                        0
                    ]
                }
            }
        }},
        {"$sort": {"_id": 1}}
    ]
    
    daily_trends = await collection.aggregate(pipeline).to_list(length=days)
    
    return {
        "period_days": days,
        "start_date": start_date.isoformat(),
        "end_date": datetime.utcnow().isoformat(),
        "daily_trends": daily_trends,
        "generated_at": datetime.utcnow().isoformat()
    }


@router.get("/surgeon-performance")
async def get_surgeon_performance() -> Dict[str, Any]:
    """Get surgeon-specific performance metrics"""
    collection = await get_surgeries_collection()
    
    pipeline = [
        {"$group": {
            "_id": "$team.surgeon",
            "total_surgeries": {"$sum": 1},
            "successful_surgeries": {"$sum": {"$cond": ["$outcomes.success", 1, 0]}},
            "surgeries_with_complications": {
                "$sum": {
                    "$cond": [
                        {"$gt": [{"$size": {"$ifNull": ["$outcomes.complications", []]}}, 0]},
                        1,
                        0
                    ]
                }
            },
            "avg_duration": {"$avg": "$procedure.duration_minutes"},
            "avg_los": {"$avg": "$outcomes.length_of_stay_days"},
            "avg_satisfaction": {"$avg": "$outcomes.patient_satisfaction"}
        }},
        {"$addFields": {
            "success_rate": {
                "$multiply": [
                    {"$divide": ["$successful_surgeries", "$total_surgeries"]},
                    100
                ]
            },
            "complication_rate": {
                "$multiply": [
                    {"$divide": ["$surgeries_with_complications", "$total_surgeries"]},
                    100
                ]
            }
        }},
        {"$sort": {"total_surgeries": -1}}
    ]
    
    surgeon_stats = await collection.aggregate(pipeline).to_list(length=100)
    
    # Round numeric values
    for stat in surgeon_stats:
        stat["success_rate"] = round(stat["success_rate"], 2)
        stat["complication_rate"] = round(stat["complication_rate"], 2)
        if stat["avg_duration"]:
            stat["avg_duration"] = round(stat["avg_duration"], 2)
        if stat["avg_los"]:
            stat["avg_los"] = round(stat["avg_los"], 2)
        if stat["avg_satisfaction"]:
            stat["avg_satisfaction"] = round(stat["avg_satisfaction"], 2)
    
    return {
        "surgeon_performance": surgeon_stats,
        "generated_at": datetime.utcnow().isoformat()
    }
