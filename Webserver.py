from flask import Flask, render_template, request
from wtforms import Form, FileField, validators
from wtforms import SelectMultipleField

import os
import random
import pandas as pd
import SMBH

app = Flask(__name__,template_folder='/home/kronos/GPFS-1/Templates')
# clear tmp directory
dir = '/home/kronos/GPFS-1/tmp'
for f in os.listdir(dir):
    os.remove(os.path.join(dir, f))

# configure the app
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['MAX_CONTENT_LENGTH'] = 64 * 1024 * 1024


class FileForm(Form):
    file = FileField('File')

class TaskForm(Form):
    tasks = SelectMultipleField('Tasks')

@app.route('/upload', methods=['GET', 'POST'])
@app.route('/identify_unit', methods=['GET', 'POST'])
def upload():
    marks = SMBH.Markbook()

    form = FileForm()
    if request.method == 'POST':
        try:
            file = request.files['file']
            # Use the secure_filename() function to generate a safe filename
            # and the os.path.join() function to join the directory and filename
            filename = str(random.randint(1000000000,9999999999))
            print(filename)
            file.save(os.path.join("/home/kronos/GPFS-1/tmp", filename+'.pdf'))
            full_path = os.path.join("/home/kronos/GPFS-1/tmp", filename+'.pdf')
            marks.extract_tables(full_path)
            print(marks.data())
            # use your module to convert the pdf to a dataframe
            return render_template('identify_unit.html', form=form, df=df)
        except Exception as e:
            return(str(e))
    return render_template('Upload.html', form=form)

def identify_unit(df):
    form = TaskForm()
    form.tasks.choices = [(task, task) for task in df["Task"]]
    # render the form template and allow the user to select the tasks
    # ...
    if request.method == 'POST':
        # get the selected tasks and their corresponding categories
        selected_tasks = request.form.getlist('tasks')
        grade_categories = [task for task in selected_tasks if request.form.get(task) == 'grade']
        unit_categories = [task for task in selected_tasks if request.form.get(task) == 'unit']
        # update the dataframe based on the user's selections
        for index, row in df.iterrows():
            task = row["Task"]
            if task in grade_categories:
                current_grade_group = task
                current_unit = None
            elif task in unit_categories:
                current_unit = task
                current_grade_group = None
            df.at[index, "Unit"] = current_unit
            df.at[index, "Grade Group"] = current_grade_group
        df["Grade Group"] = df["Grade Group"].fillna(method='ffill')
    return df



app.run(debug=True)
              

