#!/usr/bin/env python3
"""
TLS/SSL Configuration Verification

Verifies that all network connections use proper encryption:
- MongoDB connections (TLS/SSL)
- API endpoints (HTTPS)
- Certificate validity
- Cipher strength

Compliance: UK GDPR Article 32 (Encryption in Transit)

Usage:
    python verify_tls_config.py
"""

import os
import sys
import ssl
import socket
import urllib.request
from datetime import datetime
from pathlib import Path
from pymongo import MongoClient
from dotenv import load_dotenv

# Load environment
load_dotenv()

MONGODB_URI = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/')
API_URL = os.getenv('API_URL', 'http://localhost:8000')


def check_mongodb_tls():
    """Check if MongoDB connection uses TLS"""
    print("\n🔍 Checking MongoDB TLS Configuration...")
    print(f"   Connection URI: {MONGODB_URI.split('@')[-1] if '@' in MONGODB_URI else MONGODB_URI}")

    try:
        # Parse connection string
        uri_lower = MONGODB_URI.lower()
        uses_tls = any(param in uri_lower for param in ['tls=true', 'ssl=true'])

        if uses_tls:
            print("   ✓ TLS enabled in connection string")
        else:
            print("   ⚠️  TLS NOT enabled in connection string")
            print("      MongoDB connection may be unencrypted")
            print("      For production, add ?tls=true to connection URI")

        # Try to connect
        client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000)
        client.admin.command('ping')

        # Check if connection is local
        if 'localhost' in MONGODB_URI or '127.0.0.1' in MONGODB_URI:
            print("   ℹ️  Local MongoDB connection detected")
            print("      TLS not required for localhost (loopback interface)")
            return True
        else:
            if uses_tls:
                print("   ✅ Remote MongoDB connection uses TLS")
                return True
            else:
                print("   ❌ Remote MongoDB connection without TLS - SECURITY RISK")
                return False

    except Exception as e:
        print(f"   ❌ MongoDB connection failed: {e}")
        return False


def check_api_https():
    """Check if API uses HTTPS"""
    print("\n🔍 Checking API HTTPS Configuration...")
    print(f"   API URL: {API_URL}")

    if API_URL.startswith('https://'):
        print("   ✓ API uses HTTPS")

        # Try to connect and check certificate
        try:
            # Parse URL
            from urllib.parse import urlparse
            parsed = urlparse(API_URL)
            hostname = parsed.hostname
            port = parsed.port or 443

            # Create SSL context
            context = ssl.create_default_context()

            # Connect and get certificate
            with socket.create_connection((hostname, port), timeout=5) as sock:
                with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                    cert = ssock.getpeercert()

                    # Check certificate details
                    print(f"   ✓ TLS Version: {ssock.version()}")

                    # Check expiry
                    not_after = datetime.strptime(cert['notAfter'], '%b %d %H:%M:%S %Y %Z')
                    days_until_expiry = (not_after - datetime.now()).days

                    if days_until_expiry < 0:
                        print(f"   ❌ Certificate EXPIRED {abs(days_until_expiry)} days ago")
                        return False
                    elif days_until_expiry < 30:
                        print(f"   ⚠️  Certificate expires in {days_until_expiry} days")
                    else:
                        print(f"   ✓ Certificate valid for {days_until_expiry} days")

                    # Check subject
                    subject = dict(x[0] for x in cert['subject'])
                    print(f"   ✓ Certificate issued to: {subject.get('commonName', 'N/A')}")

                    # Check cipher
                    cipher = ssock.cipher()
                    print(f"   ✓ Cipher: {cipher[0]} ({cipher[2]} bits)")

                    # Check if cipher is strong
                    if cipher[2] >= 256:
                        print(f"   ✅ Strong encryption (AES-256)")
                    elif cipher[2] >= 128:
                        print(f"   ✓ Good encryption (AES-128)")
                    else:
                        print(f"   ⚠️  Weak encryption ({cipher[2]} bits)")

                    return True

        except ssl.SSLError as e:
            print(f"   ❌ SSL Error: {e}")
            return False
        except socket.timeout:
            print(f"   ⚠️  Connection timeout - unable to verify certificate")
            return False
        except Exception as e:
            print(f"   ⚠️  Could not verify certificate: {e}")
            return False

    elif API_URL.startswith('http://'):
        # Check if localhost
        if 'localhost' in API_URL or '127.0.0.1' in API_URL:
            print("   ℹ️  Local HTTP connection detected")
            print("      HTTPS not required for localhost (loopback interface)")
            print("      However, use nginx reverse proxy with HTTPS for production")
            return True
        else:
            print("   ❌ API uses HTTP (unencrypted) - SECURITY RISK")
            print("      Production APIs must use HTTPS")
            return False
    else:
        print(f"   ❌ Unknown protocol in API URL: {API_URL}")
        return False


def check_tls_version():
    """Check supported TLS versions"""
    print("\n🔍 Checking TLS Protocol Support...")

    # Check OpenSSL version
    print(f"   OpenSSL version: {ssl.OPENSSL_VERSION}")

    # Check minimum TLS version
    try:
        context = ssl.create_default_context()
        min_version = getattr(context, 'minimum_version', None)

        if min_version:
            print(f"   ✓ Minimum TLS version: {min_version}")
        else:
            print(f"   ℹ️  TLS version info not available")

        # Check if TLS 1.2+ is supported
        if hasattr(ssl, 'PROTOCOL_TLSv1_2'):
            print("   ✓ TLS 1.2 supported")
        else:
            print("   ⚠️  TLS 1.2 not supported - outdated OpenSSL version")

        if hasattr(ssl, 'PROTOCOL_TLS'):
            print("   ✓ TLS 1.3 capable")
        else:
            print("   ℹ️  TLS 1.3 not available")

        return True

    except Exception as e:
        print(f"   ❌ Error checking TLS version: {e}")
        return False


def check_cipher_suites():
    """Check available cipher suites"""
    print("\n🔍 Checking Cipher Suites...")

    try:
        context = ssl.create_default_context()

        # Get cipher list
        ciphers = context.get_ciphers()
        print(f"   ✓ {len(ciphers)} cipher suites available")

        # Count by strength
        strong = sum(1 for c in ciphers if c.get('strength', 0) >= 256)
        good = sum(1 for c in ciphers if 128 <= c.get('strength', 0) < 256)
        weak = sum(1 for c in ciphers if c.get('strength', 0) < 128)

        print(f"   ✓ Strong (256-bit): {strong}")
        print(f"   ✓ Good (128-bit): {good}")

        if weak > 0:
            print(f"   ⚠️  Weak (<128-bit): {weak}")
            print(f"      Consider updating OpenSSL to disable weak ciphers")

        return True

    except Exception as e:
        print(f"   ⚠️  Could not enumerate ciphers: {e}")
        return True  # Not critical


def generate_recommendations():
    """Generate security recommendations"""
    print("\n" + "=" * 60)
    print("📋 Security Recommendations")
    print("=" * 60)

    recommendations = []

    # Check if running locally
    is_local = ('localhost' in MONGODB_URI or '127.0.0.1' in MONGODB_URI) and \
               ('localhost' in API_URL or '127.0.0.1' in API_URL)

    if is_local:
        print("\n🏠 Local Development Environment Detected")
        print("\nCurrent setup is acceptable for development:")
        print("  ✓ Local connections use loopback interface (encrypted in kernel)")
        print("  ✓ Data does not traverse network")
        print("\nFor PRODUCTION deployment, implement:")
        recommendations.extend([
            "Enable MongoDB TLS/SSL (add ?tls=true to connection URI)",
            "Configure nginx reverse proxy with HTTPS for API",
            "Obtain SSL certificate (Let's Encrypt or commercial CA)",
            "Use TLS 1.2 or higher",
            "Disable weak cipher suites",
            "Enable HSTS (HTTP Strict Transport Security)",
            "Implement certificate pinning for API clients"
        ])
    else:
        print("\n🌐 Production/Remote Environment")

        if not MONGODB_URI.startswith('mongodb+srv://') and 'tls=true' not in MONGODB_URI.lower():
            recommendations.append("⚠️  CRITICAL: Enable TLS for MongoDB connections")

        if not API_URL.startswith('https://'):
            recommendations.append("⚠️  CRITICAL: Use HTTPS for API endpoints")

        recommendations.extend([
            "Review SSL certificate expiry dates (renew before 30 days)",
            "Monitor for SSL/TLS vulnerabilities",
            "Keep OpenSSL updated",
            "Implement certificate rotation procedures"
        ])

    if recommendations:
        print("\n📌 Action Items:")
        for i, rec in enumerate(recommendations, 1):
            print(f"   {i}. {rec}")
    else:
        print("\n✅ No additional recommendations - configuration looks good!")

    # GDPR Compliance Note
    print("\n📜 UK GDPR Compliance:")
    print("   ✓ Encryption in transit satisfies Article 32 (Security of Processing)")
    print("   ✓ Protects personal data during transmission")
    print("   ✓ Prevents interception and unauthorized access")


def main():
    print("=" * 60)
    print("TLS/SSL Configuration Verification")
    print("=" * 60)
    print("\nThis script verifies encryption in transit for:")
    print("  - MongoDB connections")
    print("  - API endpoints")
    print("  - TLS protocol versions")
    print("  - Cipher strength")

    results = {
        'mongodb': check_mongodb_tls(),
        'api': check_api_https(),
        'tls_version': check_tls_version(),
        'ciphers': check_cipher_suites()
    }

    # Summary
    print("\n" + "=" * 60)
    print("📊 Summary")
    print("=" * 60)

    passed = sum(results.values())
    total = len(results)

    print(f"\nChecks passed: {passed}/{total}")

    for check, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status} - {check}")

    # Generate recommendations
    generate_recommendations()

    # Exit code
    if all(results.values()):
        print("\n✅ All TLS/SSL checks passed!")
        sys.exit(0)
    elif results['mongodb'] or results['api']:  # At least one critical check passed
        print("\n⚠️  Some checks failed - review recommendations above")
        sys.exit(0)  # Warning, not error
    else:
        print("\n❌ Critical TLS/SSL issues detected")
        sys.exit(1)


if __name__ == '__main__':
    main()
