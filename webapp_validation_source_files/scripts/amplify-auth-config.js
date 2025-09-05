// Configuración de Amplify con Cognito y Okta
import { Amplify } from 'aws-amplify';

const amplifyConfig = {
  Auth: {
    // Cognito User Pool
    region: 'us-east-1',
    userPoolId: 'us-east-1_XXXXXXXXX', // Desde CloudFormation Output
    userPoolWebClientId: 'XXXXXXXXXXXXXXXXXXXXXXXXXX', // Desde CloudFormation Output
    
    // Identity Pool
    identityPoolId: 'us-east-1:xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx',
    
    // OAuth Configuration para Okta
    oauth: {
      domain: 'excel-pipeline-user-pool.auth.us-east-1.amazoncognito.com',
      scope: ['openid', 'email', 'profile'],
      redirectSignIn: 'https://your-app.amplifyapp.com/callback',
      redirectSignOut: 'https://your-app.amplifyapp.com/logout',
      responseType: 'code',
      
      // Configuración específica para Okta
      federationTarget: 'Okta',
      customProvider: 'Okta'
    }
  },
  
  Storage: {
    AWSS3: {
      bucket: 'excel-pipeline-data-raw',
      region: 'us-east-1',
      
      // Configuración de permisos por usuario
      customPrefix: {
        public: '',
        protected: 'protected/${cognito-identity.amazonaws.com:sub}/',
        private: 'private/${cognito-identity.amazonaws.com:sub}/'
      },
      
      // Configuración de uploads
      track: true,
      level: 'protected' // Solo el usuario puede ver sus archivos
    }
  }
};

Amplify.configure(amplifyConfig);

// Función para login con Okta
export const signInWithOkta = async () => {
  try {
    await Auth.federatedSignIn({ provider: 'Okta' });
  } catch (error) {
    console.error('Error en login con Okta:', error);
  }
};

// Función para obtener información del usuario
export const getCurrentUser = async () => {
  try {
    const user = await Auth.currentAuthenticatedUser();
    const userRole = user.attributes['custom:role'] || 'viewer';
    
    return {
      username: user.username,
      email: user.attributes.email,
      role: userRole,
      groups: user.signInUserSession.accessToken.payload['cognito:groups'] || []
    };
  } catch (error) {
    console.error('Error obteniendo usuario:', error);
    return null;
  }
};

// Función para verificar permisos
export const hasUploadPermission = async () => {
  const user = await getCurrentUser();
  return user && (user.role === 'uploader' || user.role === 'admin');
};

export default amplifyConfig;