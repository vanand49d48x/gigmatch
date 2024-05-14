import gradio as gr
import psycopg2
import openai
import json
import os

# Set your OpenAI API key

openai.api_key = os.getenv('OPENAI_API_KEY')

def get_database_connection():
    """Establish a connection to the database using environment variables."""
    return psycopg2.connect(
        dbname=os.getenv('DB_NAME'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        host=os.getenv('DB_HOST')
    )

def fetch_profiles():
    """Fetch all worker profiles from the database."""
    conn = get_database_connection()
    profiles = []
    try:
        with conn.cursor() as curs:
            curs.execute("SELECT name, about, skills, rating, trust_score, ninja_level, task_experience, availability FROM gig_workers")
            for row in curs.fetchall():
                # Check if the skills data is a string and convert it to a list if it is
                if isinstance(row[2], str):
                    skills = json.loads(row[2])
                else:
                    skills = row[2]  # Assuming it's already a list
                #printf(row[0])
                profile = {
                    "Name": row[0],
                    "About": row[1],
                    "Skills": skills,
                    "Rating": row[3],
                    "Trust Score": row[4],
                    "Ninja Level": row[5],
                    "Task Experience": row[6],
                    "Availability": row[7]
                }
                profiles.append(profile)
    finally:
        conn.close()
    return profiles

def find_top_workers(task_description):
    profiles = fetch_profiles()
    prompt = f"Rank the following profiles based on their suitability for the task: '{task_description}'. Consider their skills, experience, availability, and rating.\n\n"
    for i, profile in enumerate(profiles, start=1):
        prompt += f"{i}. Name: {profile['Name']}, Skills: {', '.join(profile['Skills'])}, Experience: {profile['Task Experience']} hours, "
        prompt += f"Rating: {profile['Rating']}, Trust Score: {profile['Trust Score']}, Availability: {profile['Availability']}\n"

    prompt += "\nList the profile names in order of best fit to least fit for the task."

    try:
        response = openai.Completion.create(
            model="gpt-3.5-turbo-instruct",
            prompt=prompt,
            max_tokens=300
        )
        return response.choices[0].text.strip() if response.choices[0].text.strip() else "No match found."
    except Exception as e:
        return f"An error occurred: {str(e)}"


# Ensure to print the prompt in your debugging to see what exactly is being sent to the model.






def main_interface(task_description):
    """Interface function for Gradio."""
    result = find_top_workers(task_description)
    if not result:
        return "No match found."
    return result

# Set up Gradio interface
iface = gr.Interface(
    fn=main_interface,
    inputs=gr.Textbox(lines=2, placeholder="Enter the task you need help with"),
    outputs="text",
    title="Gig Worker Matcher",
    description="Enter a task to find the best gig workers for the job."
)

if __name__ == "__main__":
    iface.launch()
