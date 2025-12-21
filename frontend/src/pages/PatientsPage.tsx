import { useState, useEffect } from 'react';
import { PageHeader } from '../components/PageHeader'
import { Card } from '../components/Card'
import { Button } from '../components/Button'
import api from '../services/api';

interface Patient {
  _id: string;
  record_number: string;
  nhs_number: string;
  demographics: {
    date_of_birth: string;
    age?: number;
    gender: string;
    ethnicity?: string;
    postcode?: string;
    bmi?: number;
    weight_kg?: number;
    height_cm?: number;
  };
}

interface PatientFormData {
  record_number: string;
  nhs_number: string;
  demographics: {
    date_of_birth: string;
    age?: number;
    gender: string;
    ethnicity?: string;
    postcode?: string;
    bmi?: number;
    weight_kg?: number;
    height_cm?: number;
  };
  medical_history: {
    conditions: string[];
    previous_surgeries: any[];
    medications: string[];
    allergies: string[];
    smoking_status?: string;
    alcohol_use?: string;
  };
}

export function PatientsPage() {
  const [showForm, setShowForm] = useState(false);
  const [patients, setPatients] = useState<Patient[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [editingPatient, setEditingPatient] = useState<Patient | null>(null);
  const [deleteConfirmation, setDeleteConfirmation] = useState<{ show: boolean; patient: Patient | null }>({ show: false, patient: null });
  const [deleteConfirmText, setDeleteConfirmText] = useState('');
  
  const [formData, setFormData] = useState<PatientFormData>({
    record_number: '',
    nhs_number: '',
    demographics: {
      date_of_birth: '',
      gender: 'male',
      ethnicity: '',
      postcode: '',
    },
    medical_history: {
      conditions: [],
      previous_surgeries: [],
      medications: [],
      allergies: [],
      smoking_status: 'never',
      alcohol_use: 'none',
    },
  });

  useEffect(() => {
    loadPatients();
  }, []);

  const loadPatients = async () => {
    try {
      setLoading(true);
      const response = await api.get('/patients');
      setPatients(response.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load patients');
    } finally {
      setLoading(false);
    }
  };

  const handleInputChange = (field: string, value: any) => {
    const keys = field.split('.');
    setFormData(prev => {
      const updated = { ...prev };
      let current: any = updated;
      for (let i = 0; i < keys.length - 1; i++) {
        current = current[keys[i]];
      }
      current[keys[keys.length - 1]] = value;
      return updated;
    });
  };

  const handleEdit = (patient: Patient) => {
    setEditingPatient(patient);
    setFormData({
      record_number: patient.record_number,
      nhs_number: patient.nhs_number,
      demographics: {
        date_of_birth: patient.demographics.date_of_birth,
        gender: patient.demographics.gender,
        ethnicity: patient.demographics.ethnicity || '',
        postcode: patient.demographics.postcode || '',
        age: patient.demographics.age,
        bmi: patient.demographics.bmi,
        weight_kg: patient.demographics.weight_kg,
        height_cm: patient.demographics.height_cm,
      },
      medical_history: patient.medical_history || {
        conditions: [],
        previous_surgeries: [],
        medications: [],
        allergies: [],
        smoking_status: 'never',
        alcohol_use: 'none',
      },
    });
    setShowForm(true);
    setError('');
    setSuccess('');
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setSuccess('');
    
    try {
      setLoading(true);
      if (editingPatient) {
        // Update existing patient
        await api.put(`/patients/${editingPatient.record_number}`, formData);
        setSuccess('Patient updated successfully');
      } else {
        // Create new patient
        await api.post('/patients', formData);
        setSuccess('Patient created successfully');
      }
      setShowForm(false);
      setEditingPatient(null);
      setFormData({
        record_number: '',
        nhs_number: '',
        demographics: {
          date_of_birth: '',
          gender: 'male',
          ethnicity: '',
          postcode: '',
        },
        medical_history: {
          conditions: [],
          previous_surgeries: [],
          medications: [],
          allergies: [],
          smoking_status: 'never',
          alcohol_use: 'none',
        },
      });
      loadPatients();
    } catch (err: any) {
      setError(err.response?.data?.detail || `Failed to ${editingPatient ? 'update' : 'create'} patient`);
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteClick = (patient: Patient) => {
    setDeleteConfirmation({ show: true, patient });
    setDeleteConfirmText('');
  };

  const handleDeleteConfirm = async () => {
    if (!deleteConfirmation.patient) return;
    
    // Verify user typed the correct record number
    if (deleteConfirmText !== deleteConfirmation.patient.record_number) {
      setError('Record number does not match. Deletion cancelled.');
      return;
    }

    try {
      setLoading(true);
      await api.delete(`/patients/${deleteConfirmation.patient.record_number}`);
      setSuccess(`Patient ${deleteConfirmation.patient.record_number} deleted successfully`);
      setDeleteConfirmation({ show: false, patient: null });
      setDeleteConfirmText('');
      loadPatients();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to delete patient');
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteCancel = () => {
    setDeleteConfirmation({ show: false, patient: null });
    setDeleteConfirmText('');
    setError('');
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="Patient Management"
        subtitle="Manage patient records and demographics"
        icon={
          <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
          </svg>
        }
        action={
          !showForm ? (
            <Button variant="primary" onClick={() => {
              setEditingPatient(null);
              setShowForm(true);
            }}>+ Add Patient</Button>
          ) : (
            <Button variant="secondary" onClick={() => {
              setShowForm(false);
              setEditingPatient(null);
              setFormData({
                record_number: '',
                nhs_number: '',
                demographics: {
                  date_of_birth: '',
                  gender: 'male',
                  ethnicity: '',
                  postcode: '',
                },
                medical_history: {
                  conditions: [],
                  previous_surgeries: [],
                  medications: [],
                  allergies: [],
                  smoking_status: 'never',
                  alcohol_use: 'none',
                },
              });
            }}>Cancel</Button>
          )
        }
      />

      {error && (
        <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
          {error}
        </div>
      )}

      {success && (
        <div className="mb-4 p-4 bg-green-50 border border-green-200 rounded-lg text-green-700">
          {success}
        </div>
      )}

      {showForm && (
        <Card>
          <h2 className="text-xl font-semibold mb-4">{editingPatient ? 'Edit Patient' : 'New Patient'}</h2>
          <form onSubmit={handleSubmit}>
            {/* Basic Information */}
            <div className="mb-6">
              <h3 className="text-lg font-medium mb-3 text-gray-700">Basic Information</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Record Number <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="text"
                    required
                    pattern="^\d{8}$|^IW\d{6}$"
                    title="Must be 8 digits or IW followed by 6 digits"
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    value={formData.record_number}
                    onChange={(e) => handleInputChange('record_number', e.target.value)}
                    readOnly={!!editingPatient}
                    disabled={!!editingPatient}
                  />
                  <p className="mt-1 text-xs text-gray-500">Format: 8 digits or IW + 6 digits (e.g., 12345678 or IW123456)</p>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    NHS Number <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="text"
                    required
                    pattern="^\d{3} \d{3} \d{4}$"
                    title="Must be 10 digits formatted as XXX XXX XXXX"
                    placeholder="123 456 7890"
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    value={formData.nhs_number}
                    onChange={(e) => handleInputChange('nhs_number', e.target.value)}
                    readOnly={!!editingPatient}
                    disabled={!!editingPatient}
                  />
                  <p className="mt-1 text-xs text-gray-500">Format: XXX XXX XXXX (e.g., 123 456 7890)</p>
                </div>
              </div>
            </div>

            {/* Demographics */}
            <div className="mb-6">
              <h3 className="text-lg font-medium mb-3 text-gray-700">Demographics</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Date of Birth <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="date"
                    required
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    value={formData.demographics.date_of_birth}
                    onChange={(e) => handleInputChange('demographics.date_of_birth', e.target.value)}
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Gender <span className="text-red-500">*</span>
                  </label>
                  <select
                    required
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    value={formData.demographics.gender}
                    onChange={(e) => handleInputChange('demographics.gender', e.target.value)}
                  >
                    <option value="male">Male</option>
                    <option value="female">Female</option>
                    <option value="other">Other</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Postcode
                  </label>
                  <input
                    type="text"
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    value={formData.demographics.postcode}
                    onChange={(e) => handleInputChange('demographics.postcode', e.target.value)}
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Ethnicity
                  </label>
                  <input
                    type="text"
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    value={formData.demographics.ethnicity}
                    onChange={(e) => handleInputChange('demographics.ethnicity', e.target.value)}
                  />
                </div>
              </div>
            </div>

            {/* Physical Measurements */}
            <div className="mb-6">
              <h3 className="text-lg font-medium mb-3 text-gray-700">Physical Measurements</h3>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Weight (kg)
                  </label>
                  <input
                    type="number"
                    step="0.1"
                    min="20"
                    max="300"
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    value={formData.demographics.weight_kg || ''}
                    onChange={(e) => handleInputChange('demographics.weight_kg', e.target.value ? parseFloat(e.target.value) : undefined)}
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Height (cm)
                  </label>
                  <input
                    type="number"
                    step="0.1"
                    min="100"
                    max="250"
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    value={formData.demographics.height_cm || ''}
                    onChange={(e) => handleInputChange('demographics.height_cm', e.target.value ? parseFloat(e.target.value) : undefined)}
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    BMI
                  </label>
                  <input
                    type="number"
                    step="0.1"
                    min="10"
                    max="80"
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    value={formData.demographics.bmi || ''}
                    onChange={(e) => handleInputChange('demographics.bmi', e.target.value ? parseFloat(e.target.value) : undefined)}
                  />
                </div>
              </div>
            </div>

            <div className="flex justify-between items-center gap-3">
              <div>
                {editingPatient && (
                  <Button 
                    type="button" 
                    variant="danger" 
                    onClick={() => handleDeleteClick(editingPatient)}
                  >
                    Delete Patient
                  </Button>
                )}
              </div>
              <div className="flex gap-3">
                <Button type="submit" disabled={loading} variant="primary">
                  {loading ? (editingPatient ? 'Updating...' : 'Creating...') : (editingPatient ? 'Update Patient' : 'Create Patient')}
                </Button>
                <Button 
                  type="button" 
                  variant="secondary" 
                  onClick={() => {
                    setShowForm(false);
                    setEditingPatient(null);
                  }}
                >
                  Cancel
                </Button>
              </div>
            </div>
          </form>
        </Card>
      )}

      {/* Patient List */}
      <Card>
        <h2 className="text-xl font-semibold mb-4">Patient List</h2>
        {loading && !showForm && <p className="text-gray-500">Loading...</p>}
        {!loading && patients.length === 0 && (
          <div className="text-center py-12">
            <svg className="mx-auto w-16 h-16 text-gray-300 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" />
            </svg>
            <h3 className="text-lg font-medium text-gray-900 mb-2">No Patients Yet</h3>
            <p className="text-gray-500 mb-4">Get started by adding your first patient record</p>
          </div>
        )}
        {patients.length > 0 && (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Record Number
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    NHS Number
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Date of Birth
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Gender
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Postcode
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {patients.map((patient) => (
                  <tr key={patient._id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                      {patient.record_number}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {patient.nhs_number}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {patient.demographics.date_of_birth}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 capitalize">
                      {patient.demographics.gender}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {patient.demographics.postcode || '-'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      <div className="flex items-center gap-3">
                        <button
                          onClick={() => handleEdit(patient)}
                          className="text-blue-600 hover:text-blue-800"
                          title="Edit patient"
                        >
                          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
                          </svg>
                        </button>
                        <button
                          onClick={() => handleDeleteClick(patient)}
                          className="text-red-600 hover:text-red-800"
                          title="Delete patient"
                        >
                          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                          </svg>
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}      </Card>

      {/* Delete Confirmation Modal */}
      {deleteConfirmation.show && deleteConfirmation.patient && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-md w-full mx-4">
            <div className="px-6 py-4 border-b border-gray-200">
              <div className="flex items-center gap-3">
                <div className="flex-shrink-0 w-12 h-12 rounded-full bg-red-100 flex items-center justify-center">
                  <svg className="w-6 h-6 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                  </svg>
                </div>
                <div>
                  <h3 className="text-lg font-semibold text-gray-900">Delete Patient Record</h3>
                  <p className="text-sm text-gray-500">This action cannot be undone</p>
                </div>
              </div>
            </div>
            <div className="px-6 py-4">
              <div className="mb-4">
                <p className="text-sm text-gray-700 mb-2">
                  You are about to permanently delete the patient record for:
                </p>
                <div className="bg-gray-50 rounded-md p-3 border border-gray-200">
                  <p className="text-sm font-medium text-gray-900">Record Number: {deleteConfirmation.patient.record_number}</p>
                  <p className="text-sm text-gray-600">NHS Number: {deleteConfirmation.patient.nhs_number}</p>
                  <p className="text-sm text-gray-600">DOB: {deleteConfirmation.patient.demographics.date_of_birth}</p>
                </div>
              </div>
              
              <div className="bg-red-50 border border-red-200 rounded-md p-3 mb-4">
                <p className="text-sm font-medium text-red-800 mb-2">
                  ⚠️ Warning: This will permanently delete all patient data and cannot be recovered.
                </p>
              </div>

              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  To confirm deletion, please type the patient's record number:
                  <span className="font-semibold text-red-600"> {deleteConfirmation.patient.record_number}</span>
                </label>
                <input
                  type="text"
                  value={deleteConfirmText}
                  onChange={(e) => setDeleteConfirmText(e.target.value)}
                  className="w-full border border-gray-300 rounded-md px-3 py-2 focus:ring-2 focus:ring-red-500 focus:border-transparent"
                  placeholder="Enter record number to confirm"
                  autoFocus
                />
              </div>

              {error && deleteConfirmation.show && (
                <div className="mb-4 bg-red-50 border border-red-200 text-red-700 px-3 py-2 rounded text-sm">
                  {error}
                </div>
              )}
            </div>
            <div className="px-6 py-4 bg-gray-50 rounded-b-lg flex justify-end gap-3">
              <Button
                type="button"
                variant="secondary"
                onClick={handleDeleteCancel}
                disabled={loading}
              >
                Cancel
              </Button>
              <Button
                type="button"
                variant="danger"
                onClick={handleDeleteConfirm}
                disabled={loading || deleteConfirmText !== deleteConfirmation.patient.record_number}
              >
                {loading ? 'Deleting...' : 'Delete Patient'}
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

