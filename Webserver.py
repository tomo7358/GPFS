from flask import Flask, render_template, request,g,redirect,url_for,session
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
app.config['SECRET_KEY'] = 'udOAg]!YzPC}=%WW}3"+K>E*[x7`XV&iGExmEDz>|4fbL$a51{J.VNQW7_9a4oO'
app.config['MAX_CONTENT_LENGTH'] = 64 * 1024 * 1024
# identify unit form

class FileForm(Form):
    file = FileField('File')

class TaskForm(Form):
    tasks = SelectMultipleField('Tasks')

@app.route('/upload', methods=['GET', 'POST'])


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



def upload():
    form = FileForm()
    if request.method == 'POST':
        file = request.files['file']
        filename = str(random.randint(1000000000,9999999999))
        file.save(os.path.join("/home/kronos/GPFS-1/tmp", filename+'.pdf'))
        marks = SMBH.Markbook(file)
        marks.extract_tables()
        return redirect(url_for('identify_unit'),marks=marks )
    return render_template('Upload.html', form=form)






app.run(debug=True)
              

