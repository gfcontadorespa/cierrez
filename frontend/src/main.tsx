import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { PublicClientApplication, EventType } from "@azure/msal-browser";
import { MsalProvider } from "@azure/msal-react";
import { msalConfig } from "./authConfig";
import './index.css'
import App from './App.tsx'

const msalInstance = new PublicClientApplication(msalConfig);

msalInstance.initialize().then(() => {
  // Opcional: manejar eventos de login para configurar la cuenta activa
  const accounts = msalInstance.getAllAccounts();
  if (accounts.length > 0) {
      msalInstance.setActiveAccount(accounts[0]);
  }

  msalInstance.addEventCallback((event: any) => {
      if (event.eventType === EventType.LOGIN_SUCCESS && event.payload.account) {
          const account = event.payload.account;
          msalInstance.setActiveAccount(account);
      }
  });

  createRoot(document.getElementById('root')!).render(
    <StrictMode>
      <MsalProvider instance={msalInstance}>
        <App />
      </MsalProvider>
    </StrictMode>,
  )
});
