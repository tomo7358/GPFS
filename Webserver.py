#import libraries for flask
from flask import Flask, render_template, request,g,redirect,url_for,session
from wtforms import Form, FileField, validators
from wtforms import SelectMultipleField

#import additional libraries for pdf parsing and markbook processing
import os
import random
import pandas as pd
import SMBH

#define tmp foler path
tmp_folder = '/home/kronos/GPFS-1/tmp'
#create app and set template folder
app = Flask(__name__,template_folder='/home/kronos/GPFS-1/Templates')

# clear tmp directory
dir = '/home/kronos/GPFS-1/tmp'
for f in os.listdir(dir):
    os.remove(os.path.join(dir, f))

# configure the app

#secret key for session
app.config['SECRET_KEY'] = 'udOAg]!YzPC}=%WW}3"+K>E*[x7`XV&iGExmEDz>|4fbL$a51{J.VNQW7_9a4oO'
# max file size set to 64MB
app.config['MAX_CONTENT_LENGTH'] = 64 * 1024 * 1024

#create forms for uploading files and selecting tasks
class FileForm(Form):
    file = FileField('File')

class TaskForm(Form):
    tasks = SelectMultipleField('Tasks')

class NHITaskForm(Form):
    tasks = SelectMultipleField('Tasks')

# homepage where user can upload a pdf
@app.route('/', methods=['GET', 'POST'])
def index():
    return render_template('index.html')


#upload function
@app.route('/upload', methods=['GET', 'POST'])
<<<<<<< HEAD
=======

#Identify the unit or grade group
def identify_unit(marks):
        df=marks.data()
        form = TaskForm()
        form.tasks.choices = [(task, task) for task in df["Task"]]
        if request.method == 'POST':
            selected_tasks = request.form.getlist('tasks')
            grade_categories = [task for task in selected_tasks if request.form.get(task) == 'grade']
            unit_categories = [task for task in selected_tasks if request.form.get(task) == 'unit']
            for index, row in df.iterrows():
                task = row["Task"]
                if task in grade_categories:
                    current_unit = None
                elif task in unit_categories:
                    current_unit = task
                    current_grade_group = None
                    df.at[index, "Unit"] = current_unit
                    df.at[index, "Grade Group"] = current_grade_group
                    df["Grade Group"] = df["Grade Group"].fillna(method='ffill')
                    return str(df)
        return render_template('identify_unit.html', form=form)

#upload file function
>>>>>>> ace9bb84eb3e68ab7a6c84e660febcce8442149f
def upload():
    form = FileForm()
    if request.method == 'POST':
        file = request.files['file']
        filename = str(random.randint(1000000000,9999999999))
<<<<<<< HEAD
        file.save(os.path.join(tmp_folder, filename+'.pdf'))
        
        return redirect(url_for('identify_unit', filename=filename))

#page that allows user to select which tasks are grade categories and which are unit categories
@app.route('/identify_unit/<filename>', methods=['GET', 'POST'])
def identify_unit(filename):
    # Create the full path to the pdf file
    full_path = os.path.join(tmp_folder, filename+'.pdf')
    # Create a new markbook object
    marks=SMBH.Markbook()
    # Extract the tables from the pdf
    marks.extract_tables(full_path)
    # Get the dataframe from the markbook object
    df=marks.data()
    # Create a form for selecting tasks
    form = TaskForm()
    # Populate the form with the tasks from the dataframe
    form.tasks.choices = [(task, task) for task in df["Task"]]
    current_unit = None
    if request.method == 'POST':
        grade_categories=[]
        unit_categories=[]
        # Get the selected tasks from the form
        for task in form.tasks:
            task_name = task.label.text
            if request.form.get(task_name + '_unit'):
                unit_categories.append(task_name)
            if request.form.get(task_name + '_grade'):
                grade_categories.append(task_name)

        current_unit = None
        current_grade_group = None
        # Iterate through the rows of the dataframe
        for index, row in df.iterrows():
            task = row["Task"]
            # If the task is a grade category, update the current grade group
            if task in grade_categories:
                current_grade_group = task
                current_unit = None
            # If the task is a unit category, update the current unit
            elif task in unit_categories:
                current_unit = task
                current_grade_group = None
            # Update the dataframe with the current unit and grade group
            df.at[index, "Unit"] = current_unit
            df.at[index, "Grade Group"] = current_grade_group

        # Fill in any missing values for the grade group
        df["Grade Group"] = df["Grade Group"].fillna(method='ffill')
        
        # Update the markbook object with the updated dataframe
        marks.df=df
        # Calculate the marks for each task
        marks.calculate_marks()
        marks.df.to_csv(tmp_folder + '/' + filename + '.csv', index=False)
        # Redirect to the homepage
        return redirect(url_for("identify_nhi", id=filename))
    # Get the unique tasks from the dataframe
    tasks = df['Task'].unique()
    # Create a new form for selecting tasks
    form = TaskForm()
    # Populate the form with the unique tasks
    form.tasks.choices = [(task, task) for task in tasks]

    # Render the template for identifying the unit
    return render_template('identify_unit.html', form=form)



@app.route('/identify_nhi<id>', methods=['GET', 'POST'])
def identify_nhi(id):
    df=pd.read_csv(tmp_folder + '/' + id + '.csv')
    # Create a new markbook object
    marks=SMBH.Markbook()
    #add dataframe to markbook object
    marks.df=df
    # Create a form for selecting tasks
    form = NHITaskForm()
    marks = request.args.get(marks)
    nhi_list = []
    if request.method == 'POST':
        # Get the selected tasks from the form
        for task in form.tasks:
            task_name = task.label.text
            if request.form.get(task_name):
                nhi_list.append(task_name)

        # create a new column in the dataframe to store the calculated marks
        df["Calculated Mark"] = 0
        # Iterate through the rows of the dataframe
        for index, row in df.iterrows():
            # Check if the mark is NaN
            if pd.isnull(row["Mark"]):
                # Check if the task is in the list of NHI's
                if row["Task"] in nhi_list:
                    df.at[index, "Mark"] = 0
                    df.at[index, "Calculated Mark"] = "NHI"
                else:
                    df.at[index, "Calculated Mark"] = "PASS"
        # Update the markbook object with the updated dataframe
        marks.df = df
        # Redirect to the homepage
        return redirect("/")
    # Get the tasks with NaN in the calculated marks column
    tasks_with_nan = df[pd.isnull(df["Calculated Mark"])]["Task"].unique()
    form.tasks.choices = [(task, task) for task in tasks_with_nan]
    # Render the template for identifying the NHI
    return render_template('IsNHI.html', form=form)





=======
        file.save(os.path.join("/home/kronos/GPFS-1/tmp", filename+'.pdf'))
        marks = SMBH.Markbook(file)
        marks.extract_tables()
        return redirect(url_for('identify_unit'),marks=marks )
    return render_template('Upload.html', form=form)

>>>>>>> ace9bb84eb3e68ab7a6c84e660febcce8442149f
app.run(debug=True)
              

