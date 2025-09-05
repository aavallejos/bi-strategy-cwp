# WebApp Validation Source Files

Propuesta completa para solución de carga y validación de archivos Excel con conversión a CSV y catalogación automática en AWS.

## 📁 Estructura del Proyecto

```
webapp_validation_source_files/
├── docs/                           # Documentación completa
│   ├── excel-to-csv-pipeline-solution.md    # Arquitectura principal
│   ├── implementation-guide.md              # Guía de implementación
│   ├── sso-okta-integration.md              # Integración SSO
│   └── okta-setup-guide.md                  # Configuración Okta
├── infrastructure/                 # Templates CloudFormation
│   ├── excel-pipeline-infrastructure.yaml   # Infraestructura principal
│   └── cognito-okta-infrastructure.yaml     # Autenticación SSO
└── scripts/                        # Código y configuraciones
    ├── lambda_excel_processor.py            # Función Lambda
    └── amplify-auth-config.js               # Configuración frontend
```

## 🏗️ Arquitectura de la Solución

### Pipeline Principal
```
Usuario → Okta SSO → Amplify App → S3 (raw) → Lambda → S3 (processed) → Glue Catalog
```

### Servicios AWS Utilizados
- **AWS Amplify** - Frontend web con autenticación
- **Amazon Cognito** - Federación SSO con Okta
- **Amazon S3** - Almacenamiento (raw, processed, rejected)
- **AWS Lambda** - Procesamiento y validación
- **Amazon EventBridge** - Orquestación de eventos
- **AWS Glue** - Catalogación automática
- **Amazon CloudWatch** - Monitoreo y logs

## 🚀 Características Principales

### ✅ Funcionalidades Core
- Carga de archivos Excel (.xlsx, .xls)
- Conversión automática a CSV
- Validaciones de calidad de datos
- Catalogación automática en Glue
- Manejo de errores y archivos rechazados

### 🔐 Seguridad y Autenticación
- SSO integrado con Okta
- Roles granulares (Uploader, Viewer, Admin)
- Permisos basados en usuario
- Auditoría completa de accesos

### 📊 Monitoreo y Observabilidad
- Logs centralizados en CloudWatch
- Métricas de procesamiento
- Alertas automáticas
- Dashboard de monitoreo

## 💰 Estimación de Costos

### Escenario Básico (100 archivos/mes)
- **Total**: ~$5-10 USD/mes
- S3: $1 USD
- Lambda: $1 USD
- Glue: $2 USD
- Amplify: $1 USD
- Cognito: $0.55 USD

### Escenario Empresarial (1000 archivos/mes)
- **Total**: ~$30-40 USD/mes
- Escalabilidad automática incluida

## ⏱️ Tiempo de Implementación

- **Fase 1** (MVP): 2-3 semanas
- **Fase 2** (SSO + Mejoras): 1 semana adicional
- **Total**: 3-4 semanas

## 🛠️ Implementación Rápida

### 1. Desplegar Infraestructura
```bash
aws cloudformation create-stack \
    --stack-name excel-pipeline \
    --template-body file://infrastructure/excel-pipeline-infrastructure.yaml \
    --capabilities CAPABILITY_IAM
```

### 2. Configurar Autenticación
```bash
aws cloudformation create-stack \
    --stack-name excel-pipeline-auth \
    --template-body file://infrastructure/cognito-okta-infrastructure.yaml \
    --capabilities CAPABILITY_NAMED_IAM
```

### 3. Desplegar Frontend
```bash
amplify init
amplify add hosting
amplify publish
```

## 📋 Ventajas Competitivas

### ✅ Tecnológicas
- **100% Serverless** - Sin infraestructura que mantener
- **Auto-escalable** - Maneja desde pocos archivos hasta miles
- **Costo-efectiva** - Pago solo por uso
- **Integrada** - Funciona nativamente con ecosistema AWS

### ✅ Operacionales
- **Implementación rápida** - 3-4 semanas
- **Mantenimiento mínimo** - Servicios gestionados
- **Monitoreo incluido** - CloudWatch integrado
- **Seguridad empresarial** - SSO y roles granulares

### ✅ Escalabilidad
- **Procesamiento paralelo** - Lambda concurrente
- **Almacenamiento ilimitado** - S3 escalable
- **Catalogación automática** - Glue Crawler
- **Multi-región** - Disponibilidad global

## 📞 Soporte y Mantenimiento

### Incluido en la Propuesta
- Documentación completa
- Scripts de deployment
- Configuración de monitoreo
- Guías de troubleshooting

### Servicios Adicionales
- Capacitación del equipo
- Soporte post-implementación
- Optimizaciones personalizadas
- Integraciones adicionales

---

**Contacto**: Para más información sobre la implementación de esta solución, contactar al equipo de BI Strategy CWP.