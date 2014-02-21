# Name:		PyDict.py
# Author:	Richard ROSALION
# Date:		March, 2011
# Notes:	Takes a text file dictionary (one word/phrase per line) and
#               generates a hybrid dictionary to use for password cracking
#
# Revisions:
#  1.0  4/03/2011  Initial Version
#  1.1  7/03/2011  Now saves to SQLite DB, including date password was
#                  initially exported (to allow users to add words/rules
#                  without having to completly re-run the entire dictionary)


import os,sys,sqlite3,time
from progressbar import *

# Normalise input text file? (i.e. convert to lower case)
boolNormalise = True

# Remove spaces inside the string?
boolNoSpaces = True

# Variables relating to Progress bar
widgets = [Percentage(), ' ', Bar(), ' ', FileTransferSpeed(), ' ', ETA()]


"""
Custom Error
"""
class PyDictException(Exception):
	def __init__(self, value):
		self.value = value
	def __str__(self):
		return repr(self.value)

	

"""
readInputDictionary(
        txtFileName - path to the text file to be opened
        sqLiteFileName - SQLite database to save dictionary to
)

Reads the entire contents of a text file, saving unique records to an SQLite Database
Also returns the set of unique values
"""
def readDictionaryToSQLite(txtFileName, sqLiteFileName):
        # Open Dictionary for Reading
        txtFile = openFile(txtFileName, "rt")

        # Open SQLite File
        (conn,cur) = openSQLite(sqLiteFileName)
        
        # Read input dictionary into list (must fit in memory)
        lines = txtFile.readlines()
        for i in range(len(lines)):
                # Strip leading/trailing whitespace
                lines[i] = lines[i].strip()
                # Make lowercase, if option is set
                if boolNormalise:
                        lines[i] = lines[i].lower()
                # Strip embeded spaces, if option is set
                if boolNoSpaces:
                        lines[i] = lines[i].replace(" ", "")
                # Add word to dictionary
                addWord(lines[i], conn, cur)


        # Close Open Files
        txtFile.close()
        closeSQLite(conn, cur)

        # Return retreived values (may contain duplicates)
        return lines


       

"""
addWord(
        word - string representing the word to add to the database
        conn - sqlite3.connect object representing the active connection
        cur - sqlite3.cursor object representing the active connection
        counter - reserved for future use (i.e. run commit every x words)
)
Add word to SQLite Database dictionary
"""
def addWord(word, conn, cur, counter=0):
        try:
                cur.execute("INSERT INTO dictionary (word,export) values('%s',NULL)" % word)
                #conn.commit()
        except sqlite3.IntegrityError:
                pass


"""
addWord(
        words - list of strings representing the words to add to the database
        conn - sqlite3.connect object representing the active connection
        cur - sqlite3.cursor object representing the active connection
)
Write all words in "words" list to SQLite dictionary
"""
def addWords(words, conn, cur):
        pbar = ProgressBar(widgets=widgets, maxval=len(words)).start()
        i = 0
        for i in range(len(words)):
                # Add current word to dictionary
                addWord(words[i], conn, cur, i)
                pbar.update(i)
        pbar.finish()

"""
Combinations of two dictionary words
"""
def addTwoDictWords(words, conn, cur):
        pbar = ProgressBar(widgets=widgets, maxval=len(words)**2).start()
        i = 0
        for i in range(len(words)):
                for j in range(len(words)):
                        # Add concatenation of current words to dictionary
                        addWord(words[i]+words[j], conn, cur, i)
                        pbar.update(i*j)
        pbar.finish()

"""
Combinations of three dictionary words
"""
def addThreeDictWords(words, conn, cur):
        pbar = ProgressBar(widgets=widgets, maxval=len(words)**3).start()
        i = 0
        for i in range(len(words)):
                for j in range(len(words)):
                        for k in range(len(words)):
                                # Add concatenation of current words to dictionary
                                addWord(words[i]+words[j]+words[k], conn, cur, i)
                                pbar.update(i*j*k)
        pbar.finish()


"""
Combinations of two dictionary words, with capitals for both words
"""
def addTwoDictWordsTitleCase(words, conn, cur):
        pbar = ProgressBar(widgets=widgets, maxval=len(words)**2).start()
        i = 0
        for i in range(len(words)):
                for j in range(len(words)):
                        # Add concatenation of current words to dictionary
                        addWord(words[i].capitalize()+words[j].capitalize(), conn, cur, i)
                        pbar.update(i*j)
        pbar.finish()


"""
Combinations of two dictionary words, with capitals for both words
"""
def addThreeDictWordsTitleCase(words, conn, cur):
        pbar = ProgressBar(widgets=widgets, maxval=len(words)**3).start()
        i = 0
        for i in range(len(words)):
                for j in range(len(words)):
                        for k in range(len(words)):
                                # Add concatenation of current words to dictionary
                                addWord(words[i].capitalize()+words[j].capitalize()+words[k].capitalize(), conn, cur, i)
                                pbar.update(i*j*k)
        pbar.finish()


"""
Takes input SQLite DB File, and prints all words to output file
"""
def writeSQLiteToText(sqLiteFileName, txtFileName):
        # Open Text File
        outFile = openFile(txtFileName, "w")

        # Open SQLite Database
        (conn, cur) = openSQLite(sqLiteFileName)
	
        # Execute Query
        print("Sorting Results... ", end="")
        sys.stdout.flush()
        try:
                cur.execute("SELECT word FROM dictionary WHERE export IS NULL ORDER BY word")
        except:
                print("Unable to SELECT from dictionary table")
        print("Done.")

        # Read Rows
        print("Writing dictionary to text file... ", end="")
        sys.stdout.flush()
        totalRows = 0
        while 1:
                # Grab a large number of results
                rows = cur.fetchmany()
                totalRows += len(rows)
                # If sqlite returned no results, we're done!
                if not rows:
                        break
             
                # Print word to standard output file
                for row in rows:
                        (word, ) = row
                        print(word, file=outFile)

        # Update Exported Field
        setAllExported(conn, cur)
        
        # Close SQLite Database and text file
        closeSQLite(conn, cur)
        outFile.close()

        # Finished
        print("Done! (%d new rows)" % totalRows)


                
"""
Set exported status on all rows
(next run will export NO rows)
"""
def setAllExported(conn, cur):
        # Set all rows as exported
        cur.execute("UPDATE dictionary SET export = DateTime('NOW') WHERE export IS NULL")
        conn.commit()  

"""
Reset exported status on all rows
(next run will export ALL rows)
"""
def resetAllExported(conn, cur):
        # Set all rows as not exported
        cur.execute("UPDATE dictionary SET export = NULL")
        conn.commit()        






"""
Add words to SQLite Dictionary based on all available rules
"""
def generateHybridDictionary(inputSQLiteFileName, words):
        # Open SQLite Database
        (conn,cur) = openSQLite(inputSQLiteFileName)
        
        # Write words as is
        print("\nStandard Dictionary...")
        addWords(words, conn, cur)

        # Write dictionary with two word phrases
        print("\nTwo Word Phrase Dictionary...")
        addTwoDictWords(words, conn, cur)

        # Two word phrases in title case (caps for first letter)
        print("\nTwo Word Phrase (title case) Dictionary...")
        addTwoDictWordsTitleCase(words, conn, cur)

        # Three Words
        print("\nThree Word Phrase Dictionary...")
        addThreeDictWords(words, conn, cur)
        
        # Three words title case
        print("\nThree Word Phrase (title case) Dictionary...")
        addThreeDictWordsTitleCase(words, conn, cur)

        # Close SQLite DB
        closeSQLite(conn, cur)
        print("\n")



"""
Open SQLite Database, and create dictionary table if required
"""
def openSQLite(sqLiteFileName):
        # Create/Open SQLite Database
        try:
                conn = sqlite3.connect(sqLiteFileName)
                cur = conn.cursor()
        except:
                print("Unable to create dictionary table in database %s." % (sqLiteFileName))
                raise

        # Create Table, warning if table already exists
        try:
                cur.execute("CREATE TABLE IF NOT EXISTS dictionary(word TEXT PRIMARY KEY, export INTEGER)")
                conn.commit()
        except:
                print("Dictionary table already exists, results will be appended to existing table.")
                pass

        return (conn,cur)


def closeSQLite(conn, cur):
        conn.commit()
        cur.close()


"""
Open text file for reading/writing
"""
def openFile(fileName, openType, defaultFile=sys.stdout):
        if (fileName == ""):
                fileObject = defaultFile
        else:
                try: fileObject = open(fileName, openType)
                except IOError:
                        print("Error in trying to open the file %s. Check that the file exists." % (fileName))
                        raise

        return fileObject


"""
RUN ME!!
"""

# Reset Exported Status?
if 0:
        (conn, cur) = openSQLite("dictionary.db")
        resetAllExported(conn, cur)
        closeSQLite(conn, cur)

# Generate Dictionary
words = readDictionaryToSQLite("PasswordsandUSNames.txt", "dictionary.db")
generateHybridDictionary("dictionary.db", words)
writeSQLiteToText("dictionary.db", "Dictionary " + time.strftime("%Y%m%d-%H%M%S", time.localtime()) + ".txt")
