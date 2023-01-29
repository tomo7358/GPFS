#import libraries for flask
from flask import Flask, render_template, request,redirect,url_for
from wtforms import Form, FileField, validators, SubmitField
from wtforms import SelectMultipleField
from flask_debugtoolbar import DebugToolbarExtension 
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
app.config['SECRET_KEY'] = b'udOAg]!YzPC}=%WW}3"+K>E*[x7`XV&iGExmEDz>|4fbL$a51{J.VNQW7_9a4oO'
# max file size set to 64MB
app.config['MAX_CONTENT_LENGTH'] = 64 * 1024 * 1024
toolbar = DebugToolbarExtension(app)
#create forms for uploading files and selecting tasks
class FileForm(Form):
    file = FileField('File')

class TaskForm(Form):
    tasks = SelectMultipleField('Tasks')

class NHITaskForm(Form):
    tasks = SelectMultipleField('Tasks')

class EditMarksForm(Form):
    regenerate_marks = SubmitField("Regenerate Marks")
    reset = SubmitField("Reset")

# homepage where user can upload a pdf
@app.route('/', methods=['GET', 'POST'])
def index():
    return render_template('index.html')


#upload function
@app.route('/upload', methods=['GET', 'POST'])
def upload():
    form = FileForm()
    if request.method == 'POST':
        file = request.files['file']
        filename = str(random.randint(1000000000,9999999999))
        file.save(os.path.join(tmp_folder, filename+'.pdf'))
        
        return redirect(url_for('identify_unit', filename=filename))

#page that allows user to select which tasks are grade categories and which are unit categories
@app.route('/identify_unit/<filename>', methods=['GET', 'POST'])
def identify_unit(filename):
    filename=filename
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
        # Redirect to the page for identifying the NHI's
        return redirect(url_for('identify_nhi', filename=filename))
    # Get the unique tasks from the dataframe
    tasks = df['Task'].unique()
    # Create a new form for selecting tasks
    form = TaskForm()
    # Populate the form with the unique tasks
    form.tasks.choices = [(task, task) for task in tasks]

    # Render the template for identifying the unit
    return render_template('identify_unit.html', form=form)



@app.route('/identify_nhi/<filename>', methods=['GET', 'POST'])
def identify_nhi(filename):
    df=pd.read_csv(tmp_folder + '/' + filename + '.csv')
    # Create a new markbook object
    marks=SMBH.Markbook()
    #add dataframe to markbook object
    marks.df=df
    # Create a form for selecting tasks
    nhi_list = []
    form = NHITaskForm()
    if request.method == 'POST':
       
        # Get the selected tasks from the form
        for task in form.tasks:
            task_name = task.label.text
            if request.form.get(task_name):
                nhi_list.append(task_name)
        # Iterate through the rows of the dataframe and replace if task has a NaN in the calculated mark column and is not in the nhi list than replace the NaN with a PASS
        for index, row in df.iterrows():
            if pd.isnull(row["Calculated Mark"]) and row["Task"] not in nhi_list:
                df.at[index, "Calculated Mark"] = "PASS"
            elif pd.isnull(row["Calculated Mark"]) and row["Task"] in nhi_list:
                df.at[index, "Calculated Mark"] = "0"
            else:
                pass
        # Update the markbook object with the updated dataframe
        marks.df=df
        #calculate the final mark
        df,final_mark=marks.calculate_markbook()
        return redirect(url_for('edit_marks', filename=filename,final_mark=final_mark))

    # Get the tasks with NaN in the calculated marks column
    tasks_with_nan = df[pd.isnull(df["Calculated Mark"])]["Task"].unique()
    form.tasks.choices = [(task, task) for task in tasks_with_nan]
    
    # Render the template for identifying the NHI
    return render_template('identify_nhi.html', form=form, df=df)

@app.route('/edit_marks/<filename>/<final_mark>', methods=['GET', 'POST'])
def edit_marks(filename,final_mark):
    df=pd.read_csv(tmp_folder + '/' + filename + '.csv')
    # Save a copy of the original dataframe in case the user resets the form
    if not os.path.exists(tmp_folder + '/' + filename +'-o'+ '.csv'):
        df.to_csv(tmp_folder + '/' + filename +'-o'+ '.csv', index=False)
    # Create a new markbook object
    marks=SMBH.Markbook()
    #add dataframe to markbook object
    marks.df=df
    if request.method == 'POST':
        print("Submitted")
        # Update the calculated mark for each task based on user input
        for index, row in df.iterrows():
            task = row["Task"]
            calculated_mark = request.form[task]
            print(calculated_mark)
            df.at[index, "Calculated Mark"] = calculated_mark

        # Update the markbook object with the updated dataframe
        marks.df=df
        print("Updated dataframe")
        print(df)
        df,final_mark=marks.calculate_markbook()

        print("Calculated final mark")
        # Save the updated dataframe to the CSV file
        df.to_csv(tmp_folder + '/' + filename + '.csv', index=False)
        # Redirect to the page for editing the marks
        return redirect(url_for('edit_marks', filename=filename,final_mark=final_mark))
    # Render the template with the current dataframe and final mark
    return render_template("edit.html", df=df, final_mark=final_mark)

@app.route('/reset_marks/<filename>/<final_mark>', methods=['POST'])
def reset_marks(filename,final_mark):
    # Reload the original dataframe from the CSV file
    df=pd.read_csv(tmp_folder + '/' + filename +'-o'+ '.csv')
    # Save the original dataframe to the CSV file
    df.to_csv(filename, index=False)
    # Render the template with the original dataframe and final mark
    return redirect(url_for('edit_marks', filename=filename,final_mark=final_mark))

@app.route('/delete_data/<filename>', methods=['POST'])
def delete_data(filename):
    # code to delete the data
    return redirect(url_for("/"))


app.run(debug=True,use_reloader=True)
              

