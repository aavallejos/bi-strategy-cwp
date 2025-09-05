import json
import boto3
import pandas as pd
import io
from datetime import datetime

s3_client = boto3.client('s3')
eventbridge_client = boto3.client('events')

def lambda_handler(event, context):
    """
    Procesa archivos Excel cargados en S3, los convierte a CSV y ejecuta validaciones
    """
    
    # Obtener información del archivo desde el evento S3
    bucket = event['Records'][0]['s3']['bucket']['name']
    key = event['Records'][0]['s3']['object']['key']
    
    try:
        # Descargar archivo Excel desde S3
        response = s3_client.get_object(Bucket=bucket, Key=key)
        excel_content = response['Body'].read()
        
        # Leer Excel con pandas
        df = pd.read_excel(io.BytesIO(excel_content))
        
        # Validaciones de calidad
        validation_result = validate_data(df, key)
        
        if validation_result['valid']:
            # Convertir a CSV
            csv_buffer = io.StringIO()
            df.to_csv(csv_buffer, index=False)
            
            # Subir CSV a bucket processed
            processed_key = key.replace('.xlsx', '.csv').replace('.xls', '.csv')
            processed_bucket = bucket.replace('-raw', '-processed')
            
            s3_client.put_object(
                Bucket=processed_bucket,
                Key=processed_key,
                Body=csv_buffer.getvalue(),
                ContentType='text/csv'
            )
            
            # Disparar evento para Glue Crawler
            trigger_glue_crawler(processed_bucket, processed_key)
            
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'message': 'Archivo procesado exitosamente',
                    'processed_file': f"{processed_bucket}/{processed_key}"
                })
            }
        else:
            # Mover archivo a bucket rejected
            move_to_rejected(bucket, key, validation_result['errors'])
            
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'message': 'Archivo rechazado por errores de validación',
                    'errors': validation_result['errors']
                })
            }
            
    except Exception as e:
        print(f"Error procesando archivo {key}: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }

def validate_data(df, filename):
    """Validaciones de calidad de datos"""
    errors = []
    
    # Validar que no esté vacío
    if df.empty:
        errors.append("El archivo está vacío")
    
    # Validar columnas requeridas (ejemplo)
    required_columns = ['id', 'name', 'date']  # Personalizar según necesidades
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        errors.append(f"Columnas faltantes: {missing_columns}")
    
    # Validar tipos de datos
    if 'date' in df.columns:
        try:
            pd.to_datetime(df['date'])
        except:
            errors.append("Formato de fecha inválido en columna 'date'")
    
    # Validar duplicados
    if df.duplicated().any():
        errors.append("Se encontraron filas duplicadas")
    
    return {
        'valid': len(errors) == 0,
        'errors': errors
    }

def move_to_rejected(bucket, key, errors):
    """Mueve archivo a bucket rejected con metadata de errores"""
    rejected_bucket = bucket.replace('-raw', '-rejected')
    
    # Copiar archivo
    s3_client.copy_object(
        CopySource={'Bucket': bucket, 'Key': key},
        Bucket=rejected_bucket,
        Key=key,
        Metadata={
            'errors': json.dumps(errors),
            'rejected_date': datetime.now().isoformat()
        }
    )
    
    # Eliminar archivo original
    s3_client.delete_object(Bucket=bucket, Key=key)

def trigger_glue_crawler(bucket, key):
    """Dispara evento para iniciar Glue Crawler"""
    eventbridge_client.put_events(
        Entries=[
            {
                'Source': 'excel.processor',
                'DetailType': 'File Processed',
                'Detail': json.dumps({
                    'bucket': bucket,
                    'key': key,
                    'timestamp': datetime.now().isoformat()
                })
            }
        ]
    )