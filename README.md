# IndiGG-backend Assignment

Hi! this is AkhilMujam 
# Resume is also shared in the above data
API Endpoints for the Management System 

# Registration
http://127.0.0.1:8000/register

while saving the data of the user we will be encrypting the password such that there is string protection

# Login
http://127.0.0.1:8000/login

Login is also done using JWT Authentication

# Add a new book
http://127.0.0.1:8000/add-book/

# Updation of Book Details by using Bood_ID
http://127.0.0.1:8000/update_book/{book_id}

# Deletion of any book using its ISBN Number
http://127.0.0.1:8000/delete_book/{isbn}

# Display all the Books 
http://127.0.0.1:8000/getallBooks

# Search Functionality
http://127.0.0.1:8000/search/{query}
Here the Query can be a title of the book, ISBN, or author name


# If a User Borrow Book 
http://127.0.0.1:8000/borrow/{user_token}/{book_isbn}

if the User Borrows up to 3 books then he is not allowed to borrow
and the current date is taken and made an end_date by extending 20 Days 

# Borrow Returns

http://127.0.0.1:8000/return/{user_token}/{book_isbn}

As the book is returned from the Borrowed list the Book is deleted from that user





