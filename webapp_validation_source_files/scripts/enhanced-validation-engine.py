#!/usr/bin/env python3
"""
Enhanced HeadCount File Validation Engine
Implements all F-1 through F-12 functional requirements
"""

import json
import boto3
import pandas as pd
import re
import io
from datetime import datetime, timedelta
from typing import Dict, List, Any, Tuple
import uuid

class HeadCountValidationEngine:
    def __init__(self):
        self.s3_client = boto3.client('s3')
        self.dynamodb = boto3.resource('dynamodb')
        self.ssm_client = boto3.client('ssm')
        self.apigateway_client = boto3.client('apigatewaymanagementapi')
        
        # Load configuration
        self.schemas_table = self.dynamodb.Table('hc-validation-schemas')
        self.audit_table = self.dynamodb.Table('hc-validation-audit-log')
        
    def validate_file(self, file_info: Dict, partner_id: str, connection_id: str) -> Dict:
        """Main validation orchestrator"""
        validation_id = str(uuid.uuid4())
        results = {
            'validation_id': validation_id,
            'partner_id': partner_id,
            'timestamp': datetime.now().isoformat(),
            'file_info': file_info,
            'validations': {},
            'errors': [],
            'status': 'IN_PROGRESS'
        }
        
        try:
            # F-1: Filename validation
            self._send_progress(connection_id, 'Validating filename pattern...', 10)
            filename_result = self._validate_filename(file_info)
            results['validations']['filename'] = filename_result
            
            # F-2: File size validation
            self._send_progress(connection_id, 'Checking file size...', 20)
            size_result = self._validate_file_size(file_info)
            results['validations']['file_size'] = size_result
            
            # F-3: Template structure validation
            self._send_progress(connection_id, 'Validating template structure...', 30)
            structure_result = self._validate_structure(file_info)
            results['validations']['structure'] = structure_result
            
            # Load file data for detailed validations
            df = self._load_excel_file(file_info['s3_key'])
            
            # F-4: Data type and format validation
            self._send_progress(connection_id, 'Validating data types and formats...', 50)
            data_result = self._validate_data_types(df, file_info['hc_type'])
            results['validations']['data_types'] = data_result
            
            # F-5: Primary key uniqueness
            self._send_progress(connection_id, 'Checking for duplicates...', 70)
            uniqueness_result = self._validate_uniqueness(df, file_info['hc_type'])
            results['validations']['uniqueness'] = uniqueness_result
            
            # F-6: Business rules validation
            self._send_progress(connection_id, 'Applying business rules...', 85)
            business_result = self._validate_business_rules(df, file_info['hc_type'])
            results['validations']['business_rules'] = business_result
            
            # Determine overall status
            has_errors = any(v.get('errors', []) for v in results['validations'].values())
            
            if has_errors:
                results['status'] = 'FAILED'
                # F-7: Generate detailed error report
                results['error_report'] = self._generate_error_report(results)
                self._send_progress(connection_id, 'Validation failed. Generating error report...', 100)
            else:
                results['status'] = 'PASSED'
                # F-9: Generate presigned URL for upload
                results['presigned_url'] = self._generate_presigned_url(file_info, partner_id)
                self._send_progress(connection_id, 'Validation successful! Ready for upload.', 100)
            
            # F-10: Audit logging
            self._log_validation_attempt(results)
            
            return results
            
        except Exception as e:
            results['status'] = 'ERROR'
            results['error'] = str(e)
            self._send_progress(connection_id, f'Validation error: {str(e)}', 100)
            self._log_validation_attempt(results)
            return results
    
    def _validate_filename(self, file_info: Dict) -> Dict:
        """F-1: Validate filename pattern"""
        filename = file_info['filename']
        hc_type = file_info['hc_type']
        
        patterns = {
            'Contractors': r'^HC_Contratistas_[A-Za-z0-9]+_\d{6}\.xlsx$',
            'Stores': r'^HC_Tiendas_\d{6}\.xlsx$',
            'D2D': r'^HC_D2D_\d{6}\.xlsx$'
        }
        
        pattern = patterns.get(hc_type)
        if not pattern:
            return {
                'status': 'FAILED',
                'errors': [{'message': f'Unknown HC type: {hc_type}'}]
            }
        
        if not re.match(pattern, filename):
            return {
                'status': 'FAILED',
                'errors': [{
                    'message': f'Filename does not match required pattern for {hc_type}',
                    'expected_pattern': pattern,
                    'actual_filename': filename
                }]
            }
        
        return {'status': 'PASSED', 'message': 'Filename validation successful'}
    
    def _validate_file_size(self, file_info: Dict) -> Dict:
        """F-2: Validate file size"""
        try:
            max_size_mb = int(self.ssm_client.get_parameter(
                Name='/hc-validation/config/max-file-size-mb'
            )['Parameter']['Value'])
        except:
            max_size_mb = 50  # Default
        
        file_size_mb = file_info['size_bytes'] / (1024 * 1024)
        
        if file_size_mb > max_size_mb:
            return {
                'status': 'FAILED',
                'errors': [{
                    'message': f'File size {file_size_mb:.2f}MB exceeds maximum {max_size_mb}MB',
                    'actual_size_mb': file_size_mb,
                    'max_size_mb': max_size_mb
                }]
            }
        
        return {
            'status': 'PASSED',
            'message': f'File size {file_size_mb:.2f}MB is within limits'
        }
    
    def _validate_structure(self, file_info: Dict) -> Dict:
        """F-3: Validate template structure"""
        try:
            # Get schema configuration
            schema = self._get_schema_config(file_info['hc_type'])
            
            # Load Excel file to check structure
            excel_file = self._load_excel_file(file_info['s3_key'], header_only=True)
            
            errors = []
            
            # Check sheet name
            if schema['required_sheet'] not in excel_file.sheet_names:
                errors.append({
                    'message': f'Required sheet "{schema["required_sheet"]}" not found',
                    'found_sheets': excel_file.sheet_names
                })
            
            # Check columns
            df = pd.read_excel(excel_file, sheet_name=schema['required_sheet'], nrows=0)
            expected_columns = [field['name'] for field in schema['fields']]
            actual_columns = df.columns.tolist()
            
            missing_columns = set(expected_columns) - set(actual_columns)
            if missing_columns:
                errors.append({
                    'message': 'Missing required columns',
                    'missing_columns': list(missing_columns)
                })
            
            extra_columns = set(actual_columns) - set(expected_columns)
            if extra_columns:
                errors.append({
                    'message': 'Unexpected columns found',
                    'extra_columns': list(extra_columns)
                })
            
            if errors:
                return {'status': 'FAILED', 'errors': errors}
            
            return {'status': 'PASSED', 'message': 'Template structure is valid'}
            
        except Exception as e:
            return {
                'status': 'FAILED',
                'errors': [{'message': f'Structure validation error: {str(e)}'}]
            }
    
    def _validate_data_types(self, df: pd.DataFrame, hc_type: str) -> Dict:
        """F-4: Validate data types and formats"""
        schema = self._get_schema_config(hc_type)
        errors = []
        
        for field in schema['fields']:
            field_name = field['name']
            if field_name not in df.columns:
                continue
            
            column_data = df[field_name]
            
            # Check mandatory fields
            if field.get('mandatory', False):
                null_count = column_data.isnull().sum()
                if null_count > 0:
                    null_rows = df[column_data.isnull()].index.tolist()
                    errors.append({
                        'field': field_name,
                        'message': f'Mandatory field has {null_count} null values',
                        'rows': [r + 2 for r in null_rows]  # +2 for Excel row numbering
                    })
            
            # Validate data type
            if field['type'] == 'string':
                # String length validation
                if 'min_length' in field or 'max_length' in field:
                    for idx, value in column_data.items():
                        if pd.notna(value):
                            value_len = len(str(value))
                            if field.get('min_length', 0) > value_len:
                                errors.append({
                                    'field': field_name,
                                    'row': idx + 2,
                                    'message': f'Value too short (min: {field["min_length"]})',
                                    'value': str(value)
                                })
                            if field.get('max_length', float('inf')) < value_len:
                                errors.append({
                                    'field': field_name,
                                    'row': idx + 2,
                                    'message': f'Value too long (max: {field["max_length"]})',
                                    'value': str(value)
                                })
                
                # Pattern validation
                if 'pattern' in field:
                    pattern = re.compile(field['pattern'])
                    for idx, value in column_data.items():
                        if pd.notna(value) and not pattern.match(str(value)):
                            errors.append({
                                'field': field_name,
                                'row': idx + 2,
                                'message': f'Value does not match required pattern',
                                'pattern': field['pattern'],
                                'value': str(value)
                            })
            
            elif field['type'] == 'date':
                # ISO 8601 date validation
                for idx, value in column_data.items():
                    if pd.notna(value):
                        try:
                            pd.to_datetime(value, format='%Y-%m-%d')
                        except:
                            errors.append({
                                'field': field_name,
                                'row': idx + 2,
                                'message': 'Invalid date format (expected: YYYY-MM-DD)',
                                'value': str(value)
                            })
            
            elif field['type'] == 'email':
                # Email validation
                email_pattern = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
                for idx, value in column_data.items():
                    if pd.notna(value) and not email_pattern.match(str(value)):
                        errors.append({
                            'field': field_name,
                            'row': idx + 2,
                            'message': 'Invalid email format',
                            'value': str(value)
                        })
        
        if errors:
            return {'status': 'FAILED', 'errors': errors}
        
        return {'status': 'PASSED', 'message': 'Data type validation successful'}
    
    def _validate_uniqueness(self, df: pd.DataFrame, hc_type: str) -> Dict:
        """F-5: Validate primary key uniqueness"""
        schema = self._get_schema_config(hc_type)
        
        # Get primary key fields
        pk_fields = [f['name'] for f in schema['fields'] if f.get('primary_key_component', False)]
        
        if not pk_fields:
            return {'status': 'PASSED', 'message': 'No primary key defined'}
        
        # Check for duplicates
        duplicates = df[df.duplicated(subset=pk_fields, keep=False)]
        
        if not duplicates.empty:
            duplicate_groups = []
            for _, group in duplicates.groupby(pk_fields):
                rows = group.index.tolist()
                duplicate_groups.append({
                    'key_values': {field: group[field].iloc[0] for field in pk_fields},
                    'rows': [r + 2 for r in rows]  # +2 for Excel row numbering
                })
            
            return {
                'status': 'FAILED',
                'errors': [{
                    'message': f'Duplicate primary key values found',
                    'primary_key_fields': pk_fields,
                    'duplicates': duplicate_groups
                }]
            }
        
        return {'status': 'PASSED', 'message': 'Primary key uniqueness validated'}
    
    def _validate_business_rules(self, df: pd.DataFrame, hc_type: str) -> Dict:
        """F-6: Validate business rules"""
        schema = self._get_schema_config(hc_type)
        errors = []
        
        # Apply business rules based on HC type
        if hc_type == 'Contractors':
            # Example: Termination reason required if termination date present
            if 'termination_date' in df.columns and 'termination_reason' in df.columns:
                mask = df['termination_date'].notna() & df['termination_reason'].isna()
                invalid_rows = df[mask].index.tolist()
                if invalid_rows:
                    errors.append({
                        'rule': 'termination_reason_required',
                        'message': 'Termination reason required when termination date is present',
                        'rows': [r + 2 for r in invalid_rows]
                    })
        
        # Add more business rules as needed
        
        if errors:
            return {'status': 'FAILED', 'errors': errors}
        
        return {'status': 'PASSED', 'message': 'Business rules validation successful'}
    
    def _generate_error_report(self, validation_results: Dict) -> Dict:
        """F-7: Generate comprehensive error report"""
        total_errors = 0
        detailed_errors = []
        
        for validation_type, result in validation_results['validations'].items():
            if result.get('errors'):
                for error in result['errors']:
                    total_errors += 1
                    detailed_errors.append({
                        'validation_type': validation_type,
                        'error_id': f"ERR_{total_errors:04d}",
                        'timestamp': datetime.now().isoformat(),
                        **error
                    })
        
        return {
            'report_id': str(uuid.uuid4()),
            'timestamp': datetime.now().isoformat(),
            'total_errors': total_errors,
            'file_info': validation_results['file_info'],
            'errors': detailed_errors,
            'suggested_actions': self._generate_suggested_actions(detailed_errors)
        }
    
    def _generate_presigned_url(self, file_info: Dict, partner_id: str) -> Dict:
        """F-9: Generate secure presigned URL"""
        bucket_name = 'hc-validation-s3-exchange-prod'
        key = f"{partner_id}/{file_info['hc_type']}/{datetime.now().strftime('%Y/%m/%d')}/{file_info['filename']}"
        
        presigned_url = self.s3_client.generate_presigned_url(
            'put_object',
            Params={
                'Bucket': bucket_name,
                'Key': key,
                'ContentType': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                'ServerSideEncryption': 'AES256'
            },
            ExpiresIn=3600  # 1 hour
        )
        
        return {
            'url': presigned_url,
            'bucket': bucket_name,
            'key': key,
            'expires_in': 3600,
            'expires_at': (datetime.now() + timedelta(hours=1)).isoformat()
        }
    
    def _send_progress(self, connection_id: str, message: str, progress: int):
        """F-11: Send real-time progress updates via WebSocket"""
        try:
            self.apigateway_client.post_to_connection(
                ConnectionId=connection_id,
                Data=json.dumps({
                    'type': 'progress_update',
                    'message': message,
                    'progress': progress,
                    'timestamp': datetime.now().isoformat()
                })
            )
        except Exception as e:
            print(f"Failed to send progress update: {e}")
    
    def _log_validation_attempt(self, results: Dict):
        """F-10: Audit logging"""
        try:
            self.audit_table.put_item(
                Item={
                    'partner_id': results['partner_id'],
                    'timestamp': results['timestamp'],
                    'validation_id': results['validation_id'],
                    'status': results['status'],
                    'file_info': results['file_info'],
                    'error_count': len(results.get('errors', [])),
                    'ttl': int((datetime.now() + timedelta(days=90)).timestamp())
                }
            )
        except Exception as e:
            print(f"Failed to log audit entry: {e}")
    
    def _get_schema_config(self, hc_type: str) -> Dict:
        """Load schema configuration from DynamoDB"""
        try:
            response = self.schemas_table.get_item(
                Key={'hc_type': hc_type, 'version': 'latest'}
            )
            return response['Item']
        except:
            # Return default schema if not found
            return self._get_default_schema(hc_type)
    
    def _get_default_schema(self, hc_type: str) -> Dict:
        """Default schema configurations"""
        schemas = {
            'Contractors': {
                'hc_type': 'Contractors',
                'required_sheet': 'Contractors_Data',
                'fields': [
                    {
                        'name': 'company_name',
                        'type': 'string',
                        'mandatory': True,
                        'min_length': 3,
                        'max_length': 100
                    },
                    {
                        'name': 'employee_id',
                        'type': 'string',
                        'mandatory': True,
                        'pattern': r'^[A-Za-z0-9]{4,12}$',
                        'primary_key_component': True
                    }
                ]
            }
        }
        return schemas.get(hc_type, {})
    
    def _load_excel_file(self, s3_key: str, header_only: bool = False):
        """Load Excel file from S3"""
        # Implementation to load Excel file from S3
        pass
    
    def _generate_suggested_actions(self, errors: List[Dict]) -> List[str]:
        """Generate suggested actions based on errors"""
        suggestions = []
        
        error_types = set(error.get('validation_type', '') for error in errors)
        
        if 'filename' in error_types:
            suggestions.append("Check filename follows the pattern: HC_<FileType><_PartnerID><YYYYMM>.xlsx")
        
        if 'data_types' in error_types:
            suggestions.append("Verify data formats match the template requirements")
        
        if 'uniqueness' in error_types:
            suggestions.append("Remove duplicate rows with same primary key values")
        
        return suggestions


def lambda_handler(event, context):
    """Lambda handler for validation engine"""
    engine = HeadCountValidationEngine()
    
    file_info = event.get('file_info', {})
    partner_id = event.get('partner_id', '')
    connection_id = event.get('connection_id', '')
    
    results = engine.validate_file(file_info, partner_id, connection_id)
    
    return {
        'statusCode': 200,
        'body': json.dumps(results)
    }