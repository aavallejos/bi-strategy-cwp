# Guía de Implementación: Pipeline Excel a CSV

## Pasos de Implementación

### 1. Preparación
```bash
# Clonar repositorio
git clone <repo-url>
cd bi-strategy-cwp

# Instalar AWS CLI (si no está instalado)
pip install awscli

# Configurar perfil AWS
aws configure --profile cliente-excel
```

### 2. Desplegar Infraestructura
```bash
# Desplegar stack de CloudFormation
aws cloudformation create-stack \
    --stack-name excel-pipeline-stack \
    --template-body file://scripts/excel-pipeline-infrastructure.yaml \
    --parameters ParameterKey=ProjectName,ParameterValue=cliente-excel \
    --capabilities CAPABILITY_IAM \
    --profile cliente-excel \
    --region us-east-1
```

### 3. Configurar Lambda Function
```bash
# Crear paquete de deployment
cd scripts
zip -r excel-processor.zip lambda_excel_processor.py

# Actualizar función Lambda
aws lambda update-function-code \
    --function-name cliente-excel-excel-processor \
    --zip-file fileb://excel-processor.zip \
    --profile cliente-excel
```

### 4. Crear Frontend con Amplify
```bash
# Instalar Amplify CLI
npm install -g @aws-amplify/cli

# Inicializar proyecto Amplify
amplify init

# Agregar hosting
amplify add hosting

# Desplegar
amplify publish
```

### 5. Configurar Permisos S3 para Amplify
```bash
# Obtener ARN del rol de Amplify
aws iam get-role --role-name amplify-* --profile cliente-excel

# Agregar política S3 al rol de Amplify
aws iam attach-role-policy \
    --role-name <amplify-role-name> \
    --policy-arn arn:aws:iam::aws:policy/AmazonS3FullAccess \
    --profile cliente-excel
```

## Validación de la Solución

### 1. Prueba de Carga
- Subir archivo Excel de prueba
- Verificar conversión a CSV
- Confirmar catalogación en Glue

### 2. Prueba de Validación
- Subir archivo con errores
- Verificar rechazo y logs
- Confirmar archivo en bucket rejected

### 3. Monitoreo
```bash
# Ver logs de Lambda
aws logs describe-log-groups --profile cliente-excel

# Ver métricas de S3
aws cloudwatch get-metric-statistics \
    --namespace AWS/S3 \
    --metric-name NumberOfObjects \
    --dimensions Name=BucketName,Value=cliente-excel-data-processed \
    --start-time 2024-01-01T00:00:00Z \
    --end-time 2024-01-02T00:00:00Z \
    --period 3600 \
    --statistics Sum \
    --profile cliente-excel
```

## Personalización por Cliente

### Validaciones Específicas
Editar `lambda_excel_processor.py`:
```python
# Personalizar columnas requeridas
required_columns = ['cliente_id', 'fecha', 'monto']

# Agregar validaciones específicas
def custom_validations(df):
    errors = []
    
    # Validar rangos de fechas
    if 'fecha' in df.columns:
        min_date = pd.to_datetime('2020-01-01')
        if (pd.to_datetime(df['fecha']) < min_date).any():
            errors.append("Fechas anteriores a 2020 no permitidas")
    
    return errors
```

### Configuración de Buckets
```bash
# Cambiar nombres de buckets en CloudFormation
# Editar parámetro ProjectName en el template
```

## Costos Estimados

### Escenario: 100 archivos/mes, 10MB promedio
- **S3**: $0.50/mes
- **Lambda**: $1.00/mes  
- **Glue**: $2.00/mes
- **Amplify**: $1.00/mes
- **Total**: ~$4.50/mes

### Escenario: 1000 archivos/mes, 50MB promedio
- **S3**: $5.00/mes
- **Lambda**: $8.00/mes
- **Glue**: $15.00/mes
- **Amplify**: $5.00/mes
- **Total**: ~$33.00/mes

## Mantenimiento

### Monitoreo Recomendado
- CloudWatch Alarms para errores de Lambda
- Métricas de S3 para uso de almacenamiento
- Logs de Glue Crawler para errores de catalogación

### Actualizaciones
- Revisar logs mensualmente
- Actualizar validaciones según feedback del cliente
- Optimizar performance de Lambda si es necesario