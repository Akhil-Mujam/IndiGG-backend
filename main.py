from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from pymongo import MongoClient
import bcrypt
from bson import ObjectId
import jwt  
from datetime import datetime, timedelta


app = FastAPI()

class User(BaseModel):
    username: str
    email: str
    password: str
    conform_password: str
    genre:str
    # createdAt:str
    borrowedBooks:list           
    booksHistory:list  


class UserLogin(BaseModel):
    email : str
    password : str


class add_new_book(BaseModel):
    isbn   : str
    title  : str
    author : str
    published_year : int
    quantity : int
    genre:str
    # createdAt:str


# default code for checking purpose
@app.get("/")
async def root():
    return {"message": "Hello this api for Library management"}


# connection to the mongodbatlas
conn = MongoClient("mongodb+srv://books:tW3V6uWK3mrCRmTr@cluster0.8mwlf6k.mongodb.net")
users_collection = conn.library.users  #users collection
book_collection = conn.library.books


# Registration 
@app.post("/register/")
async def register_user(user: User):

    existing_user = users_collection.find_one({"email": user.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email is already registered")
    
        
    if(user.password != user.conform_password):
        return {"message" : " password is not matching"}
    

    # Hash the password before storing it (You should use a proper password hashing library)
    hashed_password =  bcrypt.hashpw(user.password.encode('utf-8'), bcrypt.gensalt())  # hashing the password for security using bcrypt
    conform_hashed_password = bcrypt.hashpw(user.conform_password.encode('utf-8') , bcrypt.gensalt())
    print(hashed_password)
    
    doc = {
        "username": user.username,
        "email": user.email,
        "password": hashed_password.decode('utf-8'),
        "conform_password" : conform_hashed_password,
        "createdAt": str(datetime.now()),
        "borrowedBooks" : [],
        "booksHistory" : []
    }

    print(doc)
    # Insert the user document into the MongoDB collection
    result = users_collection.insert_one(doc)

    # Check if the insertion was successful
    if result.inserted_id:
        return {"message": "User registered successfully", "user_id": str(result.inserted_id)}
    else:
        raise HTTPException(status_code=500, detail="Failed to register user")



# PyJWT configuration
SECRET_KEY = "Library"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Function to create a JWT token
def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# Function to verify JWT token and return user data
def decode_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.DecodeError:
        raise HTTPException(status_code=401, detail="Token could not be decoded")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

def verify_token(token):
    try:
        decoded_token = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return decoded_token
    except jwt.ExpiredSignatureError:
        return "Token has expired"
    except jwt.InvalidTokenError:
        return "Invalid token"


# Login
@app.post("/login/")
async def login_user(user: UserLogin):
    # Find the user by email
    existing_user = users_collection.find_one({"email": user.email})


    if existing_user:
        # Verify the password
        if bcrypt.checkpw(user.password.encode('utf-8'), existing_user["password"].encode('utf-8')):
              access_token = create_access_token(data={"sub": user.email})
              return {"message": "Login successful", "access_token": access_token, "token_type": "bearer"}
    
    raise HTTPException(status_code=401, detail="Login failed, check your email and password")






#    ****************************************CRUD OPERATIONS***************************************

# Adding new books
@app.post("/add-book/")
async def add_book(
    book: add_new_book   # Get the access token from the header
):
    
    book_doc = {
        "isbn": book.isbn,
        "title": book.title,
        "author": book.author,
        "published_year": book.published_year,
        "quantity": book.quantity,
        "genre":book.genre,
        "createdAt":str(datetime.now())
    }

    # Insert the book document into the MongoDB collection
    result = book_collection.insert_one(book_doc)

    # Check if the insertion was successful
    if result.inserted_id:
        return {"message": "Book added successfully", "book_id": str(result.inserted_id)}
    else:
        raise HTTPException(status_code=500, detail="Failed to add book")




# UPDATION
@app.put("/update_book/{book_id}")
async def update(book_id : object , updated_book : add_new_book):


    existing_book = book_collection.find_one({"_id": ObjectId(book_id)})
    print("upadation ine ",existing_book)
    if not existing_book:
        raise HTTPException(status_code=404, detail="Book not found")

    
    updated_data = updated_book.dict()
    book_collection.update_one({"_id": ObjectId(book_id)}, {"$set": updated_data})

    return {"message": "Book updated successfully"}



# DELETION
@app.delete("/delete_book/{isbn}")
async def delete_book(
    isbn: str):
    
      # Check if the book with the given ID exists
    existing_book = book_collection.find_one({"isbn": isbn})
    if not existing_book:
        raise HTTPException(status_code=404, detail="Book not found")

    # Delete the book from the database
    result = book_collection.delete_one({"isbn": isbn})

    if result.deleted_count == 1:
        return {"message": "Book deleted successfully"}
    else:
        raise HTTPException(status_code=500, detail="Failed to delete book")
    

# DISPLAYING ALL DETAILS
@app.get('/getallBooks')
def getAllBooks():
    bookslist = list(book_collection.find())
    finalbooks = [{**book, "_id": str(book["_id"])} for book in bookslist]
    return {"status" : "Books Found" , "data" : finalbooks}



# SEARCH FUNCTIONALITY
@app.get('/search/{query}')               
async def searchBooks(query: str):
    try:
        
        regex_query = {"$regex": query, "$options": "i"}
        matched_books = list(book_collection.find({
            "$or": [
                {"title": regex_query},
                {"author": regex_query},
                {"isbn": regex_query},
                {"genre" : regex_query}
            ]
        }))
        if not matched_books:
            raise HTTPException(status_code=404, detail="No matching books found")
        for book in matched_books:
            book["_id"] = str(book["_id"])
        return {"status": "Books found", "data": matched_books}

    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal Server Error") from e
    

# *****************************************BORROWS****************************************

@app.post('/borrow/{user_token}/{book_isbn}')
def borrowBook(user_token: str, book_isbn: str):
    try:
        user_email = verify_token(user_token)
        emailf =  user_email["sub"] 
        user1 = users_collection.find_one({"email": emailf})
        print("User",user1)
        book1 = book_collection.find_one({"isbn": book_isbn})
        print("book",book1)
        if user1 is None:
            raise HTTPException(status_code=404, detail="User not found")
        if book1 is None:
            raise HTTPException(status_code=404, detail="Book not found")
        user1['_id'] = str(user1['_id'])
        book1['_id'] = str(book1['_id'])
        borrowedBooks = len(user1["borrowedBooks"])
        if(borrowedBooks >= 3):
            return {"status" : "Your Limit of 3 Books has been completed!!! You can borrow only 3 Books"}
        if book1["quantity"] > 0:
            book_details = {
                "isbn": book1["isbn"],
                "title": book1["title"],
                "author": book1["author"],
                "genre": book1["genre"],
                "borrowed_date": str(datetime.now()),
                "return_date": str(datetime.now() + timedelta(days=20))
            }
            user1["borrowedBooks"].append(book_details)
            user1["booksHistory"].append(book_details)
            book_collection.update_one({"isbn": book1["isbn"]}, {"$inc": {"quantity": -1}})
            users_collection.update_one({"email": user1["email"]}, {"$set": {"borrowedBooks": user1["borrowedBooks"],"booksHistory":user1["booksHistory"]}})
        else:
            raise HTTPException(status_code=400, detail="Book out of stock")
        
        return {"status" : "Transaction Successfull!!!   Borrow Successfull"}
    except:
        raise HTTPException(status_code=500, detail="Internal Server Error")
    


 #    *******************************RETURN**********************


@app.post('/return/{user_token}/{book_isbn}')
def returnBook(user_token: str, book_isbn: str):
    try:
        user_email = verify_token(user_token)
        emailf = user_email["sub"]
        user1 = users_collection.find_one({"email": emailf})
        print("User", user1)
        book1 = book_collection.find_one({"isbn": book_isbn})
        print("Book", book1)
        if user1 is None:
            raise HTTPException(status_code=404, detail="User not found")
        if book1 is None:
            raise HTTPException(status_code=404, detail="Book not found")
        
        user1['_id'] = str(user1['_id'])
        book1['_id'] = str(book1['_id'])

        index_to_remove = None
        for i, borrowed_book in enumerate(user1["borrowedBooks"]):
            if borrowed_book["isbn"] == book1["isbn"]:
                index_to_remove = i
                break
        
        if index_to_remove is not None:
            del user1["borrowedBooks"][index_to_remove]
            book_collection.update_one({"isbn": book1["isbn"]}, {"$inc": {"quantity": 1}})
            users_collection.update_one({"email": user1["email"]}, {"$set": {"borrowedBooks": user1["borrowedBooks"]}})
            return {"status": "Transaction Successfull!!!  Book returned successfully"}
        else:
            raise HTTPException(status_code=400, detail="You have not borrowed this book")
        
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal Server Error")
    



# ***********************************book RECOMMENDATION***************************************

@app.get('/api/recommend/{user_token}')
def getRecommendationBasedOnGenrendAuthor(user_token : str):
    user_email = verify_token(user_token)
    emailf = user_email["sub"]
    user1 = users_collection.find_one({"email": emailf})
    user1['_id'] = str(user1['_id'])
    books = user1["booksHistory"]
    bookslist = list(books.find())
    finalbooks = [{**book, "_id": str(book["_id"])} for book in bookslist]
    genres=list()
    for book in books:
        print(type(book))
        genres.append(book["genre"])
    filtered_books = [book for book in finalbooks if book["genre"] in genres]
    if not filtered_books:
        return {"message": "No Recommendations Found"}
    return {"status" : "Recommendation Successfull" , "Books" : filtered_books}
    
        