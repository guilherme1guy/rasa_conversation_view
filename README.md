# Introduction

Flask application that allows the visualization of conversations with a Rasa chatbot that uses MongoDB for session storage. Originally developed for Enap's (Escola Nacional de Administração Pública) Evatalk chatbot. For more open-source projects refer to [EVG Código Aberto](https://gitlab.evg.gov.br/codigo-aberto).

# Docker Image

[HERE](https://hub.docker.com/r/guilherme1guy/rasa_conversation_view)

# Configuration

You can change these environment variables to configure this application:

Mongo settings:
- MONGO_URL
- DB_NAME

Page title:
- ENV_TITLE 

Rasa saves the timestamp as UTC, set this to something else, like "America/Sao_Paulo" to change the timezone for displayed dates
- TIMEZONE

We use [Rasa Webchat](https://github.com/botfront/rasa-webchat) to talk to your bot. SOCKET_URL must be available to the user since the connection happens on the client-side. If SOCKET_URL is unset or empty, webchat will be deactivated:
- SOCKET_URL

You can specify a version for Webchat using:
- JS_SRC

Its possible to pass an initial payload (as a simulated user message) for the chatbot through:
- INIT_PAYLOAD

# Authors:

- [Guilherme Guy](https://github.com/guilherme1guy) 
- [Geovana Ramos](https://github.com/GeovanaRamos)

