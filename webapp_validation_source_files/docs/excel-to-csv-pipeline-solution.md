# Solución: Pipeline de Carga y Procesamiento de Archivos Excel

## Arquitectura Propuesta

### Servicios AWS Requeridos

1. **AWS Amplify** - Frontend web para carga de archivos
2. **Amazon S3** - Almacenamiento de archivos (raw y processed)
3. **AWS Lambda** - Procesamiento y validación
4. **Amazon EventBridge** - Orquestación de eventos
5. **AWS Glue** - Catalogación de datos
6. **Amazon CloudWatch** - Monitoreo y logs

## Flujo de Datos

```
Usuario → Amplify App → S3 (raw) → Lambda → S3 (processed) → Glue Crawler → Glue Catalog
```

## Componentes Detallados

### 1. Frontend (AWS Amplify)
- **Propósito**: Interfaz web para carga de archivos Excel
- **Características**:
  - Drag & drop de archivos
  - Validación de formato (solo .xlsx, .xls)
  - Barra de progreso
  - Historial de cargas

### 2. Almacenamiento (Amazon S3)
- **Buckets**:
  - `company-data-raw/` - Archivos Excel originales
  - `company-data-processed/` - Archivos CSV procesados
  - `company-data-rejected/` - Archivos con errores

### 3. Procesamiento (AWS Lambda)
- **Función**: `excel-processor`
- **Trigger**: S3 Event (PUT en bucket raw)
- **Funciones**:
  - Conversión Excel → CSV
  - Validación de columnas requeridas
  - Control de calidad de datos
  - Notificaciones de errores

### 4. Catalogación (AWS Glue)
- **Crawler**: Detecta nuevos archivos CSV
- **Catalog**: Registra esquemas automáticamente
- **Trigger**: EventBridge rule cuando se crea CSV

## Implementación

### Costos Estimados (mensual)
- Amplify: $1-5 USD
- S3: $1-10 USD (según volumen)
- Lambda: $0.20-2 USD
- Glue: $0.44/hora de crawler
- **Total**: ~$5-20 USD/mes

### Tiempo de Implementación
- **Fase 1** (MVP): 1-2 semanas
- **Fase 2** (Mejoras): 1 semana adicional

## Ventajas de esta Solución

✅ **Serverless**: Sin infraestructura que mantener
✅ **Escalable**: Maneja desde pocos archivos hasta miles
✅ **Costo-efectiva**: Pago por uso
✅ **Integrada**: Funciona nativamente con otros servicios AWS
✅ **Monitoreable**: CloudWatch para logs y métricas

## Alternativas Consideradas

### Opción 2: Streamlit en ECS
- Más control sobre la UI
- Requiere más mantenimiento
- Costo fijo más alto

### Opción 3: API Gateway + Lambda
- Más flexible para integraciones
- Requiere desarrollo frontend separado