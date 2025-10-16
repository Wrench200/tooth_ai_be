#!/usr/bin/env python3
"""
Fapshi Payment Integration
Handles payment processing, verification, and webhook management
"""

import os
import requests
import json
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

class FapshiPayment:
    def __init__(self):
        self.api_url = os.getenv('FAPSHI_API_URL', 'https://live.fapshi.com')
        self.api_key = os.getenv('FAPSHI_API_KEY')
        self.api_user = os.getenv('FAPSHI_API_USER')
        self.currency = 'XAF'
        self.payment_country = 'CM'  # Cameroon
        
        if not self.api_key or not self.api_user:
            raise ValueError("Fapshi API credentials not found in environment variables")
    
    def initiate_payment(self, amount, email=None, redirect_url=None, user_id=None, external_id=None, message=None):
        """
        Initiate a payment transaction
        
        Args:
            amount (int): Amount to charge in XAF
            email (str, optional): Customer email
            redirect_url (str, optional): URL to redirect after payment
            user_id (str, optional): Internal user ID
            external_id (str, optional): Transaction/order ID for reconciliation
            message (str, optional): Reason for payment
            
        Returns:
            dict: Payment initialization response
        """
        payload = {
            "amount": amount,
        }
        
        # Add optional parameters
        if email:
            payload["email"] = email
        if redirect_url:
            payload["redirectUrl"] = redirect_url
        if user_id:
            payload["userId"] = user_id
        if external_id:
            payload["externalId"] = external_id
        if message:
            payload["message"] = message
        
        headers = {
            "apiuser": self.api_user,
            "apikey": self.api_key,
            "Content-Type": "application/json"
        }
        
        try:
            print(f"🟡 FAPSHI REQUEST: {json.dumps(payload, indent=2)}")
            
            response = requests.post(
                f"{self.api_url}/initiate-pay",
                json=payload,
                headers=headers,
                timeout=30
            )
            
            print(f"🟢 FAPSHI RESPONSE: {response.status_code} - {response.text}")
            
            if response.status_code == 200:
                result = response.json()
                return {
                    'success': True,
                    'data': result
                }
            else:
                # Handle 4XX error responses
                try:
                    error_data = response.json()
                    error_message = error_data.get('message', f'Payment initiation failed ({response.status_code})')
                except:
                    error_message = f'Payment initiation failed ({response.status_code})'
                
                return {
                    'success': False,
                    'error': error_message
                }
                
        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'error': f'Network error: {str(e)}'
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'Error initiating payment: {str(e)}'
            }
    
    def get_payment_status(self, trans_id):
        """
        Get payment status
        
        Args:
            trans_id (str): Fapshi transaction ID
            
        Returns:
            dict: Payment status response
        """
        headers = {
            "apiuser": self.api_user,
            "apikey": self.api_key,
            "Content-Type": "application/json"
        }
        
        try:
            print(f"🟡 FAPSHI STATUS REQUEST: {trans_id}")
            
            response = requests.get(
                f"{self.api_url}/payment-status/{trans_id}",
                headers=headers,
                timeout=30
            )
            
            print(f"🟢 FAPSHI STATUS RESPONSE: {response.status_code} - {response.text}")
            
            if response.status_code == 200:
                result = response.json()
                
                # Handle array response format
                if isinstance(result, list) and len(result) > 0:
                    return result[0]  # Return the first transaction
                
                return result
            else:
                try:
                    error_data = response.json()
                    error_message = error_data.get('message', f'HTTP error! status: {response.status_code}')
                except:
                    error_message = f'HTTP error! status: {response.status_code}'
                
                raise Exception(error_message)
                
        except requests.exceptions.RequestException as e:
            raise Exception(f'Network error: {str(e)}')
        except Exception as e:
            raise Exception(f'Error getting payment status: {str(e)}')
    
    def verify_payment(self, trans_id):
        """
        Verify a payment transaction
        
        Args:
            trans_id (str): Fapshi transaction ID
            
        Returns:
            dict: Payment verification response
        """
        try:
            payment_data = self.get_payment_status(trans_id)
            
            if payment_data.get('status') == 'SUCCESSFUL':
                return {
                    'success': True,
                    'verified': True,
                    'payment_data': payment_data
                }
            elif payment_data.get('status') == 'FAILED':
                return {
                    'success': True,
                    'verified': False,
                    'payment_data': payment_data,
                    'error': 'Payment failed'
                }
            elif payment_data.get('status') == 'EXPIRED':
                return {
                    'success': True,
                    'verified': False,
                    'payment_data': payment_data,
                    'error': 'Payment link expired'
                }
            elif payment_data.get('status') == 'PENDING':
                return {
                    'success': True,
                    'verified': False,
                    'payment_data': payment_data,
                    'error': 'Payment still pending'
                }
            else:
                return {
                    'success': True,
                    'verified': False,
                    'payment_data': payment_data,
                    'error': f'Unknown payment status: {payment_data.get("status")}'
                }
                
        except Exception as e:
            return {
                'success': False,
                'verified': False,
                'error': str(e)
            }

# Global instance
fapshi = FapshiPayment()


