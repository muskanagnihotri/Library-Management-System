from flask import Flask, jsonify, request
from flask_mysqldb import MySQL
from datetime import date 

app = Flask(__name__)
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'navgurukul'
app.config['MYSQL_DB'] = 'library'

mysql = MySQL(app)

# Test endpoint
@app.route('/api/test', methods=['GET'])
def test_api():
    return jsonify({'message': 'API is working'})


# Create a new book
@app.route('/api/books', methods=['POST'])
def add_book():
    title = request.json['title']
    author = request.json['author']
    genre = request.json.get('genre', '')
    isbn = request.json.get('isbn', '')
    quantity = request.json.get('quantity', 0)
    publication_date = request.json.get('publication_date', None)  

    cur = mysql.connection.cursor()
    cur.execute('INSERT INTO books (title, author, genre, isbn, quantity,publication_date) VALUES (%s, %s, %s, %s, %s, %s)',
                (title, author, genre, isbn, quantity,publication_date))
    mysql.connection.commit()
    cur.close()

    return jsonify({'message': 'Book added successfully'})

# Retrieve all books
@app.route('/api/books/<int:book_id>', methods=['GET'])
def get_books(book_id):
    cur = mysql.connection.cursor()
    cur.execute('SELECT * FROM books where id=%s',(book_id,))
    book = cur.fetchone()
    cur.close()

    books_list = []
    if book:
        book_dict = {
            'id': book[0],
            'title': book[1],
            'author': book[2],
            'genre': book[3],
            'isbn': book[4],
            'quantity': book[5],
            'publication_date': book[6].isoformat() if book[6] else None
        }
        books_list.append(book_dict)

    return jsonify({'books': book})

# Update a book by ID
@app.route('/api/books/<int:book_id>', methods=['PUT'])
def update_book(book_id):
    title = request.json['title']
    author = request.json['author']
    genre = request.json.get('genre', '')
    isbn = request.json.get('isbn', '')
    quantity = request.json.get('quantity', 0)

    cur = mysql.connection.cursor()
    cur.execute('UPDATE books SET title=%s, author=%s, genre=%s, isbn=%s, quantity=%s WHERE id=%s',
                (title, author, genre, isbn, quantity, book_id))
    mysql.connection.commit()
    cur.close()

    return jsonify({'message': 'Book updated successfully'})

# Delete a book by ID
@app.route('/api/books/<int:book_id>', methods=['DELETE'])
def delete_book(book_id):
    cur = mysql.connection.cursor()
    cur.execute('DELETE FROM books WHERE id=%s', (book_id,))
    mysql.connection.commit()
    cur.close()

    return jsonify({'message': 'Book deleted successfully'})

#  Borrower Management APIs and Authentication Implementation #

# Create a new borrower
@app.route('/api/borrowers', methods=['POST'])
def add_borrower():
    name = request.json['name']
    email = request.json['email']
    phone = request.json.get('phone', '')
    address = request.json.get('address', '')

    cur = mysql.connection.cursor()
    cur.execute('INSERT INTO borrowers (name, email, phone, address) VALUES (%s, %s, %s, %s)',
                (name, email, phone, address))
    mysql.connection.commit()
    cur.close()

    return jsonify({'message': 'Borrower added successfully'})

# Retrieve all borrowers
@app.route('/api/borrowers', methods=['GET'])
def get_borrowers():
    cur = mysql.connection.cursor()
    cur.execute('SELECT * FROM borrowers')
    borrowers = cur.fetchall()
    cur.close()

    return jsonify({'borrowers': borrowers})


@app.route('/api/borrowers/<int:borrower_id>', methods=['DELETE'])
def delete_borrower(borrower_id):
    cur = mysql.connection.cursor()
    cur.execute('DELETE FROM borrowers WHERE id=%s', (borrower_id,))
    mysql.connection.commit()
    cur.close()

    return jsonify({'message': 'Borrower deleted successfully'})


# borrow a book
@app.route('/api/transactions',methods=['Post'])
def borrow_book():
    book_id=request.json['book_id']
    borrower_id=request.json['borrower_id']
    issue_date=request.json.get('issue_date',str(date.today()))
    return_date=request.json.get('return_date',None)

    cur=mysql.connection.cursor()
    cur.execute('SELECT id FROM borrowers WHERE id = %s', (borrower_id,))
    borrower = cur.fetchone()
    if not borrower:
        cur.close()
        return jsonify({'message': 'Borrower not found'}), 404


    cur.execute('select quantity from books where id=%s',(book_id,))
    book=cur.fetchone()
    if book and book[0]>0:
        cur.execute('update books set quantity=quantity-1 where id=%s',(book_id,))
        cur.execute('insert into transactions (book_id,borrower_id,issue_date,return_date) values (%s, %s, %s, %s)',
                    (book_id,borrower_id,issue_date,return_date))
        mysql.connection.commit()
        cur.close()
        return jsonify({'message':'Book borrowed successfully'})
    else:
        cur.close()
        return jsonify({'message':'Book not available'}),400
    

# return a book
@app.route('/api/transactions/return',methods=['Post'])
def return_book():
    transaction_id=request.json['transaction_id']
    cur=mysql.connection.cursor()
    cur.execute('update transactions set return_date=%s where id=%s',(str(date.today()),transaction_id))
    cur.execute('select book_id from transactions where id=%s',(transaction_id,))
    transaction=cur.fetchone()
    if transaction:
        cur.execute('update books set quantity=quantity+1 where id=%s',(transaction[0],))
        mysql.connection.commit()
        cur.close()
        return jsonify({'message':'Book returned succesfully'})
    else:
        cur.close()
        return jsonify({'message':'Transaction not found'})
    

# retrieve all transaction
@app.route('/api/transactions',methods=['GET'])
def get_transaction():
    cur=mysql.connection.cursor()
    cur.execute('select * from transactions')
    transactions=cur.fetchall()
    cur.close()
    transactions_list=[]
    for transaction in transactions:
        transactions_dict={
            'id':transaction[0],
            'book_id':transaction[1],
            'borrower_id':transaction[2],
            'issue_date':transaction[3].isoformat(),
            'return_date':transaction[4].isoformat() if transaction[4] else None

        }
        transactions_list.append(transactions_dict)
    return jsonify({'transactions':transactions_list})
    
#Advanced Search Operations and API Documentation #

# Search books by author, genre, or title
@app.route('/api/books/search', methods=['GET'])
def search_books():
    query = request.args.get('q')
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM books WHERE title LIKE %s OR author LIKE %s OR genre LIKE %s",
                ('%' + query + '%', '%' + query + '%', '%' + query + '%'))
    books = cur.fetchall()
    cur.close()

    return jsonify({'books': books})
if __name__ == '__main__':
    app.run(debug=True)
