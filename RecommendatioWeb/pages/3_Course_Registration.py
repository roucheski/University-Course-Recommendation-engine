import streamlit as st
import pandas as pd
import mysql.connector
import sklearn
from sklearn.metrics.pairwise import cosine_similarity
import base64
#from Login import username


st.set_page_config(layout="wide")    
def get_base64(bin_file):
    with open(bin_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()

def set_background(png_file):
    bin_str = get_base64(png_file)
    page_bg_img = '''
    <style>
    .stApp {
     background-image: url("data:image/png;base64,%s");
     background-size: cover;
    }
    </style>
    ''' % bin_str
    st.markdown(page_bg_img, unsafe_allow_html=True)

set_background('back4.jpg')
st.markdown("# Course Registration ")

year = st.selectbox('Year :', (1, 2, 3, 4))

semester = st.selectbox('Semester :', ('I', 'II'))

if year == 2 and semester == 'I':
    subject = ('BL', 'BT', 'CH', 'CS', 'EN', 'MB', 'MT', 'SE', 'ZL', 'BMS', 'FS', 'PH', 'HR', 'MG',
                'GL', 'ES', 'MIC', 'EC', 'ST', 'BC', 'DSC', 'FNA', 'SCI', 'AS', 'SI', 'FND','None')
    dropped_subject = st.selectbox('Dropped Subjects:', subject)
elif year == 3 and semester == 'I':
    # Add subjects for year 3 semester I
    subjects = ("General (B.Sc.)","Biology", "Botany", "Chemistry","Enviornmental Science"," Computer Science",
                "Molecular Biology and Biotechnology", "Zoology","Physics", "Geology","Statistics",
                "Mathematics","Data Science","Micro Biology","Computation and Management (CM)",'Statisticals and Operation Research (SOR)')  # Add your subjects here
    degree = st.selectbox('Select Degree Programme:', subjects)

submit = st.button("Submit",type="primary")

def connect_to_db():
    try:
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="new",
            database="recommendations"
        )
        return conn

    except mysql.connector.Error as e:
        st.error(f"Error connecting to MySQL database: {e}")
        return None

conn = connect_to_db()
if conn:
    # Fetch data from the database
    query = "SELECT * FROM student_courses"
    student_courses = pd.read_sql(query, conn)
    student_courses['RegNo'] = student_courses['RegNo'].fillna('').astype(str)  # Handle missing values and convert to string
    conn.close()



studentID_Item_matrix = student_courses.pivot_table(
    index='RegNo',
    columns=['courseCode', 'Combination', 'year'],
    aggfunc='count'
)

studentID_Item_matrix = studentID_Item_matrix.applymap(lambda x: 1 if x > 0 else 0)

user_to_user_similarity_matrix = pd.DataFrame(
    cosine_similarity(studentID_Item_matrix)
)

user_to_user_similarity_matrix.columns = studentID_Item_matrix.index
user_to_user_similarity_matrix['RegNo'] = studentID_Item_matrix.index
user_to_user_similarity_matrix = user_to_user_similarity_matrix.set_index('RegNo')



def recommend(student_id, year, semester, students_data, user_to_user_similarity_matrix):
    num_similar_students = 12

    # Convert student_id to string and strip any leading/trailing whitespaces
    student_id = str(student_id).strip()

    # Ensure that student_id exists in the index labels
    if student_id not in user_to_user_similarity_matrix.index:
        raise ValueError(f"Student ID '{student_id}' not found in the similarity matrix index.")
    # Assuming you have user_to_user_similarity_matrix available here

    # Step 1: Identify similar students for a particular student
    similar_students = user_to_user_similarity_matrix.loc[student_id].sort_values(ascending=False)[1:num_similar_students + 1].index

    # Step 2: Get unique courses for the specific year and semester for similar students
    courses_for_year_semester = students_data[
        (students_data['RegNo'].isin(similar_students)) & (students_data['year'] == year) & (
                    students_data['semester'] == semester)]['courseCode'].unique()

    # Step 3: Check if the student has taken the prerequisite courses for the recommended courses
    student_courses = students_data[students_data['RegNo'] == student_id]['courseCode'].unique()
    recommended_courses = []

    for course in courses_for_year_semester:
        prerequisites = students_data.loc[students_data['courseCode'] == course, 'Pre_requisites'].iloc[0]
        if pd.isnull(prerequisites) or prerequisites == 'NoPrerequisites':
            recommended_courses.append(course)
        else:
            prerequisites = [p.strip() for p in prerequisites.split(',')]  # Split prerequisites into a list and remove leading/trailing whitespaces
            if all(p in student_courses for p in prerequisites):
                recommended_courses.append(course)

    return recommended_courses

student_id = 's171167'
# year = 1
# semester = 'II'



if submit:
    recommended_courses = recommend(student_id, year, semester,student_courses,user_to_user_similarity_matrix)
    compulsory =  ['DSC4996','DSC4173','DSC4013']
    supplimentary = ['ST408','ST403']
    col1, col2= st.columns(2)
    with col1:
        if all(course in recommended_courses for course in compulsory):
            st.markdown("## Compulsory Courses : ")
            for course in compulsory:
                # Find the row corresponding to the current course code
                course_row = student_courses[student_courses['courseCode'] == course]
                if not course_row.empty:
                    credit = course_row['credits'].iloc[0]  # Assuming 'credit' is the column containing credits
                    courseName = course_row['courseName'].iloc[0]
                    st.markdown(f'<div style="background-color: {"#043583"}; color: {"white"}; padding: 10px; border-radius: 5px; margin-bottom: 10px;">{course} [{courseName}] - Credit: {credit} </div>', unsafe_allow_html=True)
                else:
                    st.error(f'No data found for course: {course}')

    with col2:
        if all(course in recommended_courses for course in supplimentary):
            st.markdown("## Supplimentary Courses : ")
            for course in supplimentary:
                # Find the row corresponding to the current course code
                course_row = student_courses[student_courses['courseCode'] == course]
                if not course_row.empty:
                    credit = course_row['credits'].iloc[0]  # Assuming 'credit' is the column containing credits
                    courseName = course_row['courseName'].iloc[0]
                    st.markdown(f'<div style="background-color: {"#043583"};  color: {"white"};padding: 10px; border-radius: 5px; margin-bottom: 10px;">{course} [{courseName}] - Credit: {credit} </div>', unsafe_allow_html=True)
                else:
                    st.error(f'No data found for course: {course}')
    #st.write(recommended_courses)