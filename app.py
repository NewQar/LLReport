from flask import Flask, render_template, request, redirect
import pandas as pd
import plotly.express as px
import io

app = Flask(__name__)

# Preload Users.xlsx at the start of the application
try:
    users_df = pd.read_excel('Users.xlsx')  # Adjust path if necessary
except Exception as e:
    print(f"Error loading Users.xlsx: {str(e)}")
    users_df = None

# Route to display the upload form
@app.route('/')
def index():
    return render_template('index.html')

# Route to handle file upload and processing
@app.route('/upload', methods=['POST'])
def upload_files():
    if request.method == 'POST':
        # Access the uploaded files
        learner_detail_file = request.files.get('learner_detail')
        learner_summary_file = request.files.get('learner_summary')

        # Check if files are uploaded properly
        if not learner_detail_file or not learner_summary_file:
            return "Error: Both 'Learner Detail' and 'Learner Summary' files are required!"

        if users_df is None:
            return "Error: Could not load 'Users.xlsx'. Please check the file and try again."

        try:
            # Read the files into memory as Pandas DataFrames
            learner_detail_df = pd.read_csv(io.StringIO(learner_detail_file.read().decode('utf-8')))
            learner_summary_df = pd.read_csv(io.StringIO(learner_summary_file.read().decode('utf-8')))
        except Exception as e:
            return f"Error reading files: {str(e)}"

        # Process the data
        try:
            division_progress, team_progress, account_activations = process_data(learner_detail_df, learner_summary_df, users_df)
        except Exception as e:
            return f"Error processing data: {str(e)}"

        # Create visualizations
        try:
            division_graph = create_visualizations(division_progress, 'Division', 'Progress', 'Division Progress')
            team_graph = create_visualizations(team_progress, 'Team', 'Progress', 'Team Progress')
        except Exception as e:
            return f"Error creating visualizations: {str(e)}"

        # Pass the visualization to the frontend
        return render_template('results.html', division_graph=division_graph, team_graph=team_graph, activations=account_activations)

    return redirect('/')

# Function to process the data
def process_data(learner_detail_df, learner_summary_df, users_df):
    # Merge LearnerDetail with Users on the email column (C for LearnerDetail)
    learner_detail_df['Email'] = learner_detail_df.iloc[:, 2]  # Column C is the 3rd column
    users_df['Email'] = users_df['email']  # Assuming 'email' is the column for matching
    
    # Merge the data to get department and team for each user
    merged_df = pd.merge(learner_detail_df, users_df[['Email', 'department', 'team']], on='Email', how='left')

    # Filter out users without departments or teams
    merged_df = merged_df.dropna(subset=['department', 'team'])

    # Group by division (department) and team, calculate the average progress
    division_progress = merged_df.groupby('department')['Progress'].mean().reset_index()
    team_progress = merged_df.groupby('team')['Progress'].mean().reset_index()

    # Count account activations from LearnerSummary
    account_activations = learner_summary_df['activated'].sum()  # Assuming there's an 'Activated' column

    return division_progress, team_progress, account_activations

# Function to create visualizations using Plotly
def create_visualizations(df, x_column, y_column, title):
    fig = px.bar(df, x=x_column, y=y_column, title=title)
    return fig.to_html(full_html=False)

if __name__ == "__main__":
    app.run(debug=True)
