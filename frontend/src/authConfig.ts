import { LogLevel } from "@azure/msal-browser";
import type { Configuration } from "@azure/msal-browser";

export const msalConfig: Configuration = {
    auth: {
        clientId: import.meta.env.VITE_MICROSOFT_CLIENT_ID || "",
        authority: "https://login.microsoftonline.com/common",
        redirectUri: window.location.origin, // Default redirect URI
    },
    cache: {
        cacheLocation: "sessionStorage", // This configures where your cache will be stored
    },
    system: {	
        loggerOptions: {	
            loggerCallback: (level, message, containsPii) => {	
                if (containsPii) {		
                    return;		
                }		
                switch (level) {
                    case LogLevel.Error:
                        console.error(message);
                        return;
                    case LogLevel.Warning:
                        console.warn(message);
                        return;
                }	
            }	
        }	
    }
};

export const loginRequest = {
    scopes: ["User.Read", "email", "profile", "openid"]
};
