# Guía de Configuración Okta SSO

## 1. Configuración en Okta

### Crear Aplicación SAML en Okta
1. **Admin Console** → Applications → Create App Integration
2. **Sign-in method**: SAML 2.0
3. **App name**: Excel Pipeline App

### Configuración SAML
```
Single sign on URL: https://excel-pipeline-user-pool.auth.us-east-1.amazoncognito.com/saml2/idpresponse
Audience URI (SP Entity ID): urn:amazon:cognito:sp:us-east-1_XXXXXXXXX
Name ID format: EmailAddress
Application username: Email
```

### Attribute Statements
```
Name: http://schemas.xmlsoap.org/ws/2005/05/identity/claims/emailaddress
Value: user.email

Name: http://schemas.xmlsoap.org/ws/2005/05/identity/claims/givenname  
Value: user.firstName

Name: http://schemas.xmlsoap.org/ws/2005/05/identity/claims/surname
Value: user.lastName

Name: custom:role
Value: user.role (custom attribute)
```

### Group Attribute Statements (Opcional)
```
Name: custom:groups
Value: isMemberOfGroupName("Excel-Uploaders") ? "uploader" : "viewer"
```

## 2. Configuración en AWS

### Desplegar Stack de Cognito
```bash
aws cloudformation create-stack \
    --stack-name excel-pipeline-auth \
    --template-body file://scripts/cognito-okta-infrastructure.yaml \
    --parameters \
        ParameterKey=ProjectName,ParameterValue=excel-pipeline \
        ParameterKey=OktaDomain,ParameterValue=company.okta.com \
        ParameterKey=OktaMetadataURL,ParameterValue=https://company.okta.com/app/exk.../sso/saml/metadata \
    --capabilities CAPABILITY_NAMED_IAM \
    --profile cliente-excel
```

### Obtener URLs de Cognito
```bash
# Obtener User Pool ID
aws cloudformation describe-stacks \
    --stack-name excel-pipeline-auth \
    --query 'Stacks[0].Outputs[?OutputKey==`UserPoolId`].OutputValue' \
    --output text \
    --profile cliente-excel

# Obtener dominio de Cognito
aws cognito-idp describe-user-pool \
    --user-pool-id us-east-1_XXXXXXXXX \
    --query 'UserPool.Domain' \
    --profile cliente-excel
```

## 3. Configuración de Roles en Okta

### Crear Grupos en Okta
- **Excel-Uploaders**: Usuarios que pueden subir archivos
- **Excel-Viewers**: Usuarios que solo pueden ver
- **Excel-Admins**: Administradores completos

### Asignar Atributo de Rol
```javascript
// En Okta Expression Language
isMemberOfGroupName("Excel-Admins") ? "admin" : 
isMemberOfGroupName("Excel-Uploaders") ? "uploader" : "viewer"
```

## 4. Testing de Integración

### Verificar SAML Response
```bash
# Usar herramientas como SAML Tracer o browser dev tools
# Verificar que los attributes lleguen correctamente
```

### Test de Login
1. Acceder a Amplify App
2. Click en "Sign in with Okta"
3. Redirect a Okta
4. Login con credenciales Okta
5. Redirect de vuelta a app con tokens

### Verificar Permisos S3
```javascript
// En la app, verificar que el usuario puede subir archivos
import { Storage } from 'aws-amplify';

const uploadFile = async (file) => {
  try {
    const result = await Storage.put(`uploads/${file.name}`, file, {
      level: 'protected',
      contentType: file.type
    });
    console.log('Upload exitoso:', result);
  } catch (error) {
    console.error('Error en upload:', error);
  }
};
```

## 5. Troubleshooting

### Errores Comunes
- **Invalid SAML Response**: Verificar URLs y metadata
- **Access Denied**: Revisar IAM roles y policies
- **Attribute Mapping**: Verificar attribute statements en Okta

### Logs para Debug
```bash
# CloudWatch Logs de Cognito
aws logs describe-log-groups \
    --log-group-name-prefix "/aws/cognito" \
    --profile cliente-excel

# Ver eventos de autenticación
aws logs filter-log-events \
    --log-group-name "/aws/cognito/userpools/us-east-1_XXXXXXXXX" \
    --start-time 1640995200000 \
    --profile cliente-excel
```

## 6. Costos Adicionales

### Cognito Pricing
- **MAU (Monthly Active Users)**: $0.0055 por MAU
- **SAML Federation**: Sin costo adicional
- **Ejemplo**: 100 usuarios = $0.55/mes

### Okta Pricing
- Según plan de Okta del cliente
- Generalmente ya incluido en licencia empresarial