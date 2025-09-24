# React + Vite

This template provides a minimal setup to get React working in Vite with HMR and some ESLint rules.

Currently, two official plugins are available:

- [@vitejs/plugin-react](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react) uses [Babel](https://babeljs.io/) for Fast Refresh
- [@vitejs/plugin-react-swc](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react-swc) uses [SWC](https://swc.rs/) for Fast Refresh

## Expanding the ESLint configuration

If you are developing a production application, we recommend using TypeScript with type-aware lint rules enabled. Check out the [TS template](https://github.com/vitejs/vite/tree/main/packages/create-vite/template-react-ts) for information on how to integrate TypeScript and [`typescript-eslint`](https://typescript-eslint.io) in your project.


# Break The Monotony Workout App

### The edited description is below:
A full-stack web application that generates random workout routines from a user-created list of exercises. It helps users avoid monotony by providing diverse exercise options based on their chosen body part and available equipment.

## Features

- **Dynamic Workout Generation:** Select a specific body part and a number of exercises to generate a new workout routine.
- **Exercise Management:** Add, edit, or delete exercises, body parts, and equipment.
- **Database Refresh:** A quick way to keep the database updated with any new exercises in the exercisedb api.
- **Responsive Design:** A clean, easy-to-use interface that works on both desktop and mobile devices.

## Technologies Used

* **Frontend:** React, HTML, CSS
* **Backend:** Python, Flask
* **Database:** MongoDB
* **Development Tools:** Axios for API requests

## Installation

To run this project locally, follow these steps:

1.  **Clone the repository:**
    ```bash
    git clone [Your-Repo-URL]
    ```
2.  **Navigate to the backend directory and set up the Python environment:**
    ```bash
    cd btm_workout
    # Create and activate a virtual environment
    python -m venv venv
    source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
    # Install Python dependencies
    pip install -r requirements.txt
    ```
3.  **Navigate to the frontend directory and install dependencies:**
    ```bash
    cd client
    npm install
    ```
4.  **Start the Flask backend server:**
    ```bash
    cd ..
    python flask_server.py
    ```
5.  **Start the React development server:**
    ```bash
    cd client
    npm run dev
    ```

## Deployment

This application is built with a backend (Python/Flask) and a frontend (React). The frontend can be deployed to a static hosting service like GitHub Pages. The backend, however, needs to be deployed to a separate server (e.g., Heroku, Vercel, or a custom VPS).

---

### **2. Deploying the Frontend with GitHub Pages**

GitHub Pages is a great way to show off your front-end code. We'll use the `gh-pages` package to automate the deployment.

1.  **Open your `package.json` file in the `client` directory.**

2.  **Add a `homepage` key** to the file, pointing to your GitHub repository's URL.

    ```json
    "homepage": "http://[Your-GitHub-Username].github.io/[Your-Repo-Name]",
    ```
    Replace `[Your-GitHub-Username]` and `[Your-Repo-Name]` with your actual username and repository name.

3.  **Install the `gh-pages` package** by running this command from your `client` directory:

    ```bash
    npm install --save-dev gh-pages
    ```

4.  **Add a `predeploy` and `deploy` script** to the `scripts` section of your `package.json` file:

    ```json
    "scripts": {
        "dev": "vite",
        "build": "vite build",
        "lint": "eslint . --ext js,jsx --report-unused-disable-directives --max-warnings 0",
        "preview": "vite preview",
        "predeploy": "npm run build",
        "deploy": "gh-pages -d dist"
    },
    ```
    The `predeploy` script will run the build process automatically before the `deploy` script.

5.  **Run the deployment command:**
    ```bash
    npm run deploy
    ```

    This command will create a `gh-pages` branch in your repository and push your compiled `dist` folder to it.

6.  **Configure GitHub Pages:**
    * Go to your repository on GitHub.
    * Click on **Settings**.
    * In the left-hand menu, click on **Pages**.
    * Under "Build and deployment," change the **Source** to **`gh-pages`** and the **folder** to **`/ (root)`**.
    * Click **Save**.

Your app will be live at the URL you specified in your `package.json` file. Remember, only the frontend will work there; the API calls will fail unless your backend is also live somewhere.