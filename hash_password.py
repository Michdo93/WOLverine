import bcrypt

def hash_password():
    password = input("Enter your password: ")

    hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

    print("Hashed password:", hashed.decode('utf-8'))

if __name__ == "__main__":
    hash_password()
