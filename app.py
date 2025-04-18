from flask import Flask, render_template, request, redirect
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os
from dotenv import load_dotenv

import boto3
from botocore.exceptions import NoCredentialsError
from werkzeug.utils import secure_filename
import uuid


app = Flask(__name__)


# Load environment variables
load_dotenv()

# Get MySQL credentials from .env
MYSQL_USER = os.getenv('MYSQL_USER')
MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD')

# Database Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@localhost/flask_blog'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # Suppress warning

# Initialize Database
db = SQLAlchemy(app)

# Configure S3 client
s3 = boto3.client(
    's3',
    aws_access_key_id=os.getenv('AWS_ACCESS_KEY'),
    aws_secret_access_key=os.getenv('AWS_SECRET_KEY'),
    region_name=os.getenv('AWS_REGION')
)

class BlogPost(db.Model):
    __tablename__ = 'BlogPost'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    author = db.Column(db.String(20), nullable=False, default='N/A')
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    cover_image_url = db.Column(db.String(200))

    def __repr__(self):
        return 'Blog post ' + str(self.id)

@app.route('/')
def index():
    all_posts = BlogPost.query.order_by(BlogPost.date_posted).all()
    return render_template('index.html', posts=all_posts)

@app.route('/posts', methods=['GET', 'POST'])
def posts():

    if request.method == 'POST':
        post_title = request.form['title']
        post_content = request.form['content']
        post_author = request.form['author']
        cover_image = request.files.get('cover_image')  # Get the uploaded file
        cover_image_url = None

        if cover_image:
            try:
                # Generate a unique filename
                filename = f"{uuid.uuid4()}_{secure_filename(cover_image.filename)}"
                # Upload to S3
                s3.upload_fileobj(
                    cover_image,
                    os.getenv('S3_BUCKET_NAME'),
                    filename,
                    ExtraArgs={'ContentType': cover_image.content_type}
                )
                # Generate the public URL
                cover_image_url = f"https://{os.getenv('S3_BUCKET_NAME')}.s3.amazonaws.com/{filename}"
            except NoCredentialsError:
                return "AWS credentials not found", 400
            except Exception as e:
                return str(e), 500

        new_post = BlogPost(
            title=post_title,
            content=post_content,
            author=post_author,
            cover_image_url=cover_image_url  # Save URL to database
        )

        db.session.add(new_post)
        db.session.commit()
        return redirect('/')
    else:
        all_posts = BlogPost.query.order_by(BlogPost.date_posted).all()[:-1]
        return render_template('posts.html', posts=all_posts)

@app.route('/posts/delete/<int:id>')
def delete(id):
    post = BlogPost.query.get_or_404(id)
    db.session.delete(post)
    db.session.commit()
    return redirect('/')

@app.route('/posts/edit/<int:id>', methods=['GET', 'POST'])
def edit(id):
    
    post = BlogPost.query.get_or_404(id)

    if request.method == 'POST':
        post.title = request.form['title']
        post.author = request.form['author']
        post.content = request.form['content']
        cover_image = request.files.get('cover_image')
        if cover_image:
            try:
                filename = f"{uuid.uuid4()}_{secure_filename(cover_image.filename)}"
                s3.upload_fileobj(
                    cover_image,
                    os.getenv('S3_BUCKET_NAME'),
                    filename,
                    ExtraArgs={'ContentType': cover_image.content_type}
                )
                post.cover_image_url = f"https://{os.getenv('S3_BUCKET_NAME')}.s3.amazonaws.com/{filename}"
            except Exception as e:
                return str(e), 500

        db.session.commit()
        return redirect('/')
    else:
        return render_template('edit.html', post=post)


if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)