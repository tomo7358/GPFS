from flask import Flask, render_template, request
from wtforms import Form, FileField, validators
import os
import random
import pandas as pd
import SMBH

app = Flask(__name__,template_folder='/home/kronos/GPFS/Templates')

app.config['SECRET_KEY'] = 'your_secret_key'
app.config['MAX_CONTENT_LENGTH'] = 64 * 1024 * 1024

class FileForm(Form):
    file = FileField('File')

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    form = FileForm()
    if request.method == 'POST':
        file = request.files['file']
        # Use the secure_filename() function to generate a safe filename
        # and the os.path.join() function to join the directory and filename
        filename = str(random.randint(1000000000,9999999999))
        print(filename)
        file.save(os.path.join("/home/kronos/GPFS/tmp", filename+'.pdf'))
        # use your module to convert the pdf to a dataframe
        return "File uploaded successfully"
    return render_template('Upload.html', form=form)



if __name__ == 'main':
    app.run(debug=True)
              

