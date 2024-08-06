import pickle
from collections import UserDict
import re
from datetime import datetime, timedelta


# Field Classes

class Field:
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return str(self.value)


class Name(Field):
    def __init__(self, value):
        super().__init__(value)


class Phone(Field):
    def __init__(self, value):
        if not self._validate(value):
            raise ValueError("Phone number must be 10 digits.")
        super().__init__(value)

    def _validate(self, phone_number):
        return bool(re.match(r'^\d{10}$', phone_number))


class Birthday(Field):
    def __init__(self, value):
        if not self._validate(value):
            raise ValueError("Invalid date format. Use DD.MM.YYYY")
        super().__init__(value)

    def _validate(self, birthday):
        try:
            datetime.strptime(birthday, '%d.%m.%Y')
            return True
        except ValueError:
            return False

    def to_date(self):
        return datetime.strptime(self.value, '%d.%m.%Y').date()


# Record Class

class Record:
    def __init__(self, name):
        self.name = Name(name)
        self.phones = []
        self.birthday = None

    def add_phone(self, phone_number):
        self.phones.append(Phone(phone_number))

    def remove_phone(self, phone_number):
        phone_to_remove = self.find_phone(phone_number)
        if phone_to_remove:
            self.phones.remove(phone_to_remove)

    def edit_phone(self, old_phone_number, new_phone_number):
        phone_to_edit = self.find_phone(old_phone_number)
        if phone_to_edit:
            self.add_phone(new_phone_number)
            self.remove_phone(old_phone_number)
        else:
            raise ValueError("Old phone does not exist so it is cannot be edited")

    def find_phone(self, phone_number):
        for phone in self.phones:
            if phone.value == phone_number:
                return phone
        return None

    def add_birthday(self, birthday):
        self.birthday = Birthday(birthday)

    def show_birthday(self):
        if self.birthday:
            return f"Birthday: {self.birthday.value}"
        return "Birthday not set."

    def days_to_birthday(self):
        if not self.birthday:
            return None
        today = datetime.now().date()
        next_birthday = self.birthday.to_date().replace(year=today.year)
        if today > next_birthday:
            next_birthday = next_birthday.replace(year=today.year + 1)
        return (next_birthday - today).days

    def __str__(self):
        phones_str = "; ".join(str(phone) for phone in self.phones)
        birthday_str = f", birthday: {self.birthday}" if self.birthday else ""
        return f"Contact name: {self.name}, phones: {phones_str}{birthday_str}"


# AddressBook Class

class AddressBook(UserDict):
    def add_record(self, record):
        self.data[record.name.value] = record

    def find(self, name):
        return self.data.get(name)

    def delete(self, name):
        if name in self.data:
            del self.data[name]

    def get_upcoming_birthdays(self):
        today = datetime.now().date()
        upcoming_birthdays = []

        for record in self.data.values():
            if record.birthday:
                birthday = record.birthday.to_date()
                birthday = birthday.replace(year=today.year)

                # Check next year if birthday is already passed
                if birthday < today:
                    birthday = birthday.replace(year=today.year + 1)

                days_until_birthday = (birthday - today).days
                if days_until_birthday <= 7:
                    if birthday.weekday() == 5:  # Saturday
                        days_until_birthday += 2
                    if birthday.weekday() == 6:  # Sunday
                        days_until_birthday += 1
                    congratulation_date = today + timedelta(days=days_until_birthday)
                    upcoming_birthdays.append(
                        {"name": record.name.value, "congratulation_date": congratulation_date.strftime("%Y.%m.%d")})

        return upcoming_birthdays


# Decorator for handling input errors

def input_error(func):
    def inner(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except KeyError:
            return "Contact not found."
        except ValueError as e:
            return str(e)
        except IndexError:
            return "Enter user name."

    return inner


# Command Handlers

@input_error
def add_contact(args, book: AddressBook):
    if len(args) != 2:
        raise ValueError("Give me name and phone please.")
    name, phone = args
    record = book.find(name)
    message = "Contact updated."
    if record is None:
        record = Record(name)
        book.add_record(record)
        message = "Contact added."
    if phone:
        record.add_phone(phone)
    return message


@input_error
def change_contact(args, book: AddressBook):
    if len(args) != 3:
        raise ValueError("Give me name, old phone, and new phone please.")
    name, old_phone, new_phone = args
    record = book.find(name)
    if record is None:
        raise KeyError
    record.edit_phone(old_phone, new_phone)
    return "Phone number updated."


@input_error
def show_phone(args, book: AddressBook):
    if len(args) != 1:
        raise ValueError("Give me name please.")
    name = args[0]
    record = book.find(name)
    if record is None:
        raise KeyError
    return "; ".join(str(phone) for phone in record.phones)


@input_error
def show_all(book: AddressBook):
    return "\n".join(str(record) for record in book.data.values())


@input_error
def add_birthday(args, book: AddressBook):
    if len(args) != 2:
        raise ValueError("Give me name and birthday please.")
    name, birthday = args
    record = book.find(name)
    if record is None:
        raise KeyError
    record.add_birthday(birthday)
    return "Birthday added."


@input_error
def show_birthday(args, book: AddressBook):
    if len(args) != 1:
        raise ValueError("Give me name please.")
    name = args[0]
    record = book.find(name)
    if record is None:
        raise KeyError
    return record.show_birthday()


@input_error
def birthdays(args, book: AddressBook):
    if len(args) != 0:
        raise ValueError("This command does not require arguments.")
    upcoming_birthdays = book.get_upcoming_birthdays()
    if not upcoming_birthdays:
        return "No upcoming birthdays in the next week."
    return "\n".join(
        f"Upcoming birthday: {user['name']} on {user['congratulation_date']}" for user in upcoming_birthdays)


# Serialization Functions

def save_data(book, filename="addressbook.pkl"):
    with open(filename, "wb") as f:
        pickle.dump(book, f)


def load_data(filename="addressbook.pkl"):
    try:
        with open(filename, "rb") as f:
            return pickle.load(f)
    except FileNotFoundError:
        return AddressBook()


# Input Parsing Function

def parse_input(user_input):
    parts = user_input.strip().split()
    command = parts[0].lower()
    args = parts[1:]
    return command, args


# Main Function

def main():
    book = load_data()
    print("Welcome to the assistant bot!")
    while True:
        user_input = input("Enter a command: ")
        command, args = parse_input(user_input)

        if command in ["close", "exit"]:
            save_data(book)
            print("Good bye!")
            break

        elif command == "hello":
            print("How can I help you?")

        elif command == "add":
            print(add_contact(args, book))

        elif command == "change":
            print(change_contact(args, book))

        elif command == "phone":
            print(show_phone(args, book))

        elif command == "all":
            print(show_all(book))

        elif command == "add-birthday":
            print(add_birthday(args, book))

        elif command == "show-birthday":
            print(show_birthday(args, book))

        elif command == "birthdays":
            print(birthdays(args, book))

        else:
            print("Invalid command.")


if __name__ == "__main__":
    main()
