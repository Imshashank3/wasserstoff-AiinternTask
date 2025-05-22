"""
Deployment guide for the Document Research & Theme Identification Chatbot.
"""

# Deployment Guide

This guide provides instructions for deploying the Document Research & Theme Identification Chatbot on various platforms.

## Prerequisites

Before deployment, ensure you have:
- A complete, tested application
- All dependencies listed in requirements.txt
- Environment variables configured
- Necessary API keys for language models

## Option 1: Render

[Render](https://render.com/) offers a simple deployment process with free tiers available.

### Steps:

1. Create a Render account if you don't have one
2. From your dashboard, click "New" and select "Web Service"
3. Connect your GitHub repository
4. Configure the service:
   - Name: `document-theme-chatbot` (or your preferred name)
   - Environment: `Python 3`
   - Build Command: `pip install -r backend/requirements.txt`
   - Start Command: `cd backend && uvicorn app.main:app --host 0.0.0.0 --port $PORT`
5. Add environment variables:
   - Click "Advanced" and add all variables from your .env file
6. Click "Create Web Service"

Your application will be deployed and available at the URL provided by Render.

## Option 2: Railway

[Railway](https://railway.app/) provides a developer-friendly platform with a generous free tier.

### Steps:

1. Create a Railway account
2. Create a new project and select "Deploy from GitHub repo"
3. Connect and select your repository
4. Configure the deployment:
   - Root Directory: `/`
   - Build Command: `pip install -r backend/requirements.txt`
   - Start Command: `cd backend && uvicorn app.main:app --host 0.0.0.0 --port $PORT`
5. Add environment variables:
   - Go to the "Variables" tab
   - Add all variables from your .env file
6. Deploy the application

Railway will provide a URL for your deployed application.

## Option 3: Replit

[Replit](https://replit.com/) is ideal for educational purposes and quick demos.

### Steps:

1. Create a Replit account
2. Create a new Repl and select "Import from GitHub"
3. Enter your repository URL
4. Configure the Repl:
   - Language: Python
   - Run Command: `cd backend && pip install -r requirements.txt && uvicorn app.main:app --host 0.0.0.0 --port 8080`
5. Add environment variables:
   - Go to the "Secrets" tab in the left sidebar
   - Add all variables from your .env file
6. Click "Run"

Your application will be available at the URL provided by Replit.

## Option 4: Hugging Face Spaces

[Hugging Face Spaces](https://huggingface.co/spaces) is perfect for AI applications.

### Steps:

1. Create a Hugging Face account
2. Go to Spaces and click "Create new Space"
3. Configure your Space:
   - Owner: Your username
   - Space name: `document-theme-chatbot` (or your preferred name)
   - License: Choose appropriate license
   - SDK: Gradio or Streamlit (depending on your frontend)
4. Clone the Space repository
5. Add your application files
6. Create a `requirements.txt` file in the root directory
7. Create an `app.py` file that imports and runs your application
8. Push changes to the Space repository

Your application will be deployed and available at `https://huggingface.co/spaces/[username]/[space-name]`.

## Option 5: Vercel

[Vercel](https://vercel.com/) is excellent for frontend-heavy applications.

### Steps:

1. Create a Vercel account
2. Install the Vercel CLI: `npm i -g vercel`
3. Create a `vercel.json` file in your project root:
   ```json
   {
     "version": 2,
     "builds": [
       {
         "src": "backend/app/main.py",
         "use": "@vercel/python"
       }
     ],
     "routes": [
       {
         "src": "/(.*)",
         "dest": "backend/app/main.py"
       }
     ]
   }
   ```
4. Deploy using the CLI:
   ```bash
   vercel
   ```
5. Follow the prompts to configure your project
6. Add environment variables through the Vercel dashboard

Your application will be deployed and available at the URL provided by Vercel.

## Considerations for Production Deployment

When deploying to production, consider the following:

1. **Database Persistence**: Ensure your vector database and document storage are persistent
2. **API Rate Limiting**: Implement rate limiting for public-facing APIs
3. **Authentication**: Add user authentication for multi-user environments
4. **Monitoring**: Set up logging and monitoring for application health
5. **Scaling**: Configure auto-scaling for handling varying loads
6. **Backup**: Implement regular backups of your data

## Troubleshooting

Common deployment issues and solutions:

1. **Missing Dependencies**: Ensure all dependencies are in requirements.txt
2. **Environment Variables**: Verify all required environment variables are set
3. **Port Configuration**: Make sure the application listens on the port provided by the platform
4. **Memory Limits**: Be aware of memory limits on free tiers, especially for vector databases
5. **Timeout Issues**: Increase timeout settings for long-running operations

For platform-specific issues, refer to their respective documentation and support channels.
