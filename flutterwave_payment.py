#!/usr/bin/env python3
"""
Flutterwave Payment Integration
Handles payment processing, verification, and webhook management
"""

import os
import requests
import json
import hashlib
import hmac
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

class FlutterwavePayment:
    def __init__(self):
        self.secret_key = os.getenv('FLUTTERWAVE_SECRET_KEY')
        self.public_key = os.getenv('FLUTTERWAVE_PUBLIC_KEY')
        self.base_url = "https://api.flutterwave.com/v3"
        
        if not self.secret_key or not self.public_key:
            raise ValueError("Flutterwave keys not found in environment variables")
    
    def initiate_payment(self, amount, email, phone_number, name, tx_ref, currency="NGN", redirect_url=None):
        """
        Initiate a payment transaction
        
        Args:
            amount (float): Amount to charge
            email (str): Customer email
            phone_number (str): Customer phone number
            name (str): Customer name
            tx_ref (str): Unique transaction reference
            currency (str): Currency code (default: NGN)
            redirect_url (str): URL to redirect after payment
            
        Returns:
            dict: Payment initialization response
        """
        payload = {
            "tx_ref": tx_ref,
            "amount": str(amount),
            "currency": currency,
            "redirect_url": redirect_url or f"{os.getenv('BASE_URL', 'http://localhost:8080')}/payment/callback",
            "customer": {
                "email": email,
                "phone_number": phone_number,
                "name": name
            },
            "customizations": {
                "title": "Brand AI Payment",
                "description": "Payment for brand generation services",
                "logo": "https://your-logo-url.com/logo.png"
            }
        }
        
        headers = {
            "Authorization": f"Bearer {self.secret_key}",
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/payments",
                json=payload,
                headers=headers
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('status') == 'success':
                    return {
                        'success': True,
                        'payment_url': result['data']['link'],
                        'tx_ref': tx_ref,
                        'flw_ref': result['data']['flw_ref']
                    }
                else:
                    return {
                        'success': False,
                        'message': result.get('message', 'Payment initiation failed')
                    }
            else:
                return {
                    'success': False,
                    'message': f'HTTP {response.status_code}: {response.text}'
                }
                
        except Exception as e:
            return {
                'success': False,
                'message': f'Error initiating payment: {str(e)}'
            }
    
    def verify_payment(self, transaction_id):
        """
        Verify a payment transaction
        
        Args:
            transaction_id (str): Flutterwave transaction ID
            
        Returns:
            dict: Payment verification response
        """
        headers = {
            "Authorization": f"Bearer {self.secret_key}",
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.get(
                f"{self.base_url}/transactions/{transaction_id}/verify",
                headers=headers
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('status') == 'success':
                    data = result['data']
                    return {
                        'success': True,
                        'transaction_id': data.get('id'),
                        'tx_ref': data.get('tx_ref'),
                        'amount': data.get('amount'),
                        'currency': data.get('currency'),
                        'status': data.get('status'),
                        'payment_type': data.get('payment_type'),
                        'customer_email': data.get('customer', {}).get('email'),
                        'customer_name': data.get('customer', {}).get('name')
                    }
                else:
                    return {
                        'success': False,
                        'message': result.get('message', 'Payment verification failed')
                    }
            else:
                return {
                    'success': False,
                    'message': f'HTTP {response.status_code}: {response.text}'
                }
                
        except Exception as e:
            return {
                'success': False,
                'message': f'Error verifying payment: {str(e)}'
            }
    
    def verify_webhook_signature(self, payload, signature):
        """
        Verify webhook signature for security
        
        Args:
            payload (str): Raw request body
            signature (str): Webhook signature header
            
        Returns:
            bool: True if signature is valid
        """
        try:
            # Create HMAC SHA256 hash
            expected_signature = hmac.new(
                self.secret_key.encode('utf-8'),
                payload.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            
            return hmac.compare_digest(expected_signature, signature)
        except Exception:
            return False
    
    def process_webhook(self, payload, signature):
        """
        Process webhook from Flutterwave
        
        Args:
            payload (dict): Webhook payload
            signature (str): Webhook signature
            
        Returns:
            dict: Processing result
        """
        # Verify signature
        if not self.verify_webhook_signature(json.dumps(payload), signature):
            return {
                'success': False,
                'message': 'Invalid webhook signature'
            }
        
        # Extract payment data
        event = payload.get('event')
        data = payload.get('data', {})
        
        if event == 'charge.completed':
            # Payment was successful
            return {
                'success': True,
                'event': event,
                'transaction_id': data.get('id'),
                'tx_ref': data.get('tx_ref'),
                'amount': data.get('amount'),
                'status': data.get('status'),
                'customer_email': data.get('customer', {}).get('email')
            }
        elif event == 'charge.failed':
            # Payment failed
            return {
                'success': False,
                'event': event,
                'message': 'Payment failed',
                'tx_ref': data.get('tx_ref')
            }
        else:
            return {
                'success': False,
                'message': f'Unhandled event: {event}'
            }

# Global instance
flutterwave = FlutterwavePayment() 