# SpecSense Frontend

This is a Next.js 14 web application using the App Router. It serves as the frontend for the SpecSense construction specification intelligence system.

## Setup

1. Copy `.env.local.example` to `.env.local` and set your backend API URL:
   ```bash
   cp .env.local.example .env.local
   # Edit .env.local and set NEXT_PUBLIC_API_URL
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Run the development server:
   ```bash
   npm run dev
   ```

Open [http://localhost:3000](http://localhost:3000) with your browser to see the result.

## Deploying to Vercel

The easiest way to deploy your Next.js app is to use the [Vercel Platform](https://vercel.com/new?utm_medium=default-template&filter=next.js&utm_source=create-next-app&utm_campaign=create-next-app-readme).

1. Push this code to a GitHub repository.
2. Go to [Vercel](https://vercel.com) and import the repository.
3. Important: In the Vercel project settings, add the Environment Variable:
   - Name: `NEXT_PUBLIC_API_URL`
   - Value: `https://aneeshdhavade-specsense.hf.space`
4. Click **Deploy**. Vercel will automatically build and deploy your application.
