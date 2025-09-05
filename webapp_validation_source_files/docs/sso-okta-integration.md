# Integración SSO con Okta

## Arquitectura con Autenticación

```
Usuario → Okta SSO → Amplify (Auth) → S3 Upload → Lambda → Pipeline
```

## Servicios Adicionales Requeridos

1. **Amazon Cognito** - Identity Provider federado
2. **AWS IAM Identity Center** - Gestión de acceso SSO
3. **Okta** - Identity Provider externo

## Configuración SSO

### 1. AWS IAM Identity Center
```bash
# Habilitar IAM Identity Center
aws sso-admin create-instance \
    --name "ExcelPipelineSSO" \
    --profile cliente-excel
```

### 2. Amazon Cognito User Pool
- **Propósito**: Federar con Okta
- **Configuración**: SAML 2.0 Identity Provider
- **Scopes**: openid, email, profile

### 3. Okta Configuration
- **Application Type**: SAML 2.0 Web App
- **Single Sign On URL**: Cognito endpoint
- **Audience URI**: Cognito User Pool ID

## Flujo de Autenticación

1. Usuario accede a Amplify App
2. Redirected a Okta login
3. Okta valida credenciales
4. SAML assertion a Cognito
5. Cognito genera JWT tokens
6. Amplify recibe tokens
7. Usuario autenticado accede a app

## Roles y Permisos

### Roles por Tipo de Usuario
- **Uploader**: Solo carga archivos
- **Viewer**: Ve historial y logs
- **Admin**: Gestiona usuarios y configuración