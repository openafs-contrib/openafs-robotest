## Creating a Test Suite

AFS Robotest's test suites are organized into two trees, client and server. The client tree has sub-trees that handle a multitude of client facing tests. Similar to the client tree, the server tree contains sub-trees with server side test suites.

The test suites, or sub-trees, organize each test by their common process. The name for each suite describes the common process. For example, a group of tests that stress AFS's limitations would go into a test suite named "stress.robot" because the common process is stress testing.

Create new test suites using the above organization.
To create a new test suite, give the suite a name that represents the tests it will contain. Test suites always end in *.robot.
Next, include the settings that the suite will use. Typically for AFS Robotest that includes resource, suite setup, and suite teardown. This section is included in every test suite.
The third step in test suite creation is to include any variables that will be used in more than one test case. Variables such as the volume name or the testpath should be included in this section. This section is not included in every test suite.
The keyword section follows the varibales. This section usually includes test suite setup and teardown. This setup and teardown is different from the one that is included in the second step. This setup logs in and creates a volume and the teardown removes the volume and logs out. This section is not included in every test suite.
The final step to creating a new test suite is to add tests.

### Writing a Test

1. Give the test a name that describes what the test proves or disproves. A good name for a test that creates a new file in a directory is "Create New File in a Directory."
2. Become familiar with the builtin keywords found in the Robot Framework documentation. These keywords are necessary when OpenAFS specific keywords need to be developed. New keywords get put into thei$
3. Next, start to write the test. It is very important that the test case be independent of the other cases in the suite to make debugging easier. For the example in step 1 the test looks similar to th$
  +Create a variable for the new directory.
  +Create a variable for the new file.
  +Check that the directory does not exist.
  +Check that the file does not exist.
  +Create the directory.
  +Create the file in the new directory.
  +Check that the file exists.
  +Remove the file.
  +Remove the directory.
  +Check that the directory does not exist.
  +Check that the file does not exist.
It is important to check that a file does not exist before creation. It is also important to make sure that it does not exist after removal. Checks can and should be used in every test case to make deb$

### Things to Remember While Creating a Test

Ask these questions:
  *What specifically should this test prove or disprove?
  *What will make this test independent of other tests within in the suite?
  *Will this test require additional keywords not found in the builtin Robot Framework keywords?

Keep these tips in mind:
  +Keep the test cases independent.
  +Test suite and test case names should be short, but as descriptive as possible.
  +If a test case exceeds fifteen lines consider creating new keywords.
  +When writing tests, pay attention to the number of spaces. In some cases Robot Framework must have two or more blank spaces between the keyword and the variables. If a program fails that should succeed, check the spacing.
  +Additional documentation can be found [here](https://github.com/robotframework/HowToWriteGoodTestCases/blob/master/HowToWriteGoodTestCases.rst)

## Testing a New Test

Before writing and running a new test, make sure that AFS Robotest is error free. Run the old tests a few times before adding a new one.

Once the test is written and saved, there are two ways to test it. The first way is to run all of the tests. The second way is to only run the test suite that the new test is in. The first method is best to make sure the tests outside of the suite remain error free.

**Common reasons for error:**
  *The spacing is incorrect. Most often, there are to few spaces between command inputs. For instance, the first command below has one space in between the two inputs and throws an error. The second command has two spaces between the inputs and is accepted by AFS and Robotest.
    Should Not Contain    ${output}*volume
    Should Not Contain    ${output}**volume
  *The command is wrong. If there are required parts to an AFS specific command missing, or there are parts missing for a Robotest keyword, Robotest will throw an error.
  *The keyword should expect a false outcome rather than a true outcome. This happens most often in checks like "Should Contain" or "Should Not Contain." First, review the man page for the expected outcome again. If that does not match then check the keywords man page for its expected outcome. Sometimes the keywords output does not match the expected output.
  *Check the spelling.

Test failure is a great opportunity to use AFS Robotest's web feature because it shows the output of each line within the test case up to the line where the test fails. Frequently, using this tool shows the source of the error. However, it does not always show the exact line where the true error occurred.

## Creating New Keywords

The OpenAFS keyword library is still growing. Adding new keywords keeps the number of lines in a test case to a minimum and allows for a more thorough test case. OpenAFS keywords can be found in this directory:
    ~/openafs-robotest/libraries/OpenAFSLibrary/OpenAFSLibrary/keywords

Writing a new keyword is like creating a test suite and writing a test. It is important to give the new keyword a name that describes what is happening in as few words as possible, that make sense. This is possibly the hardest part of developing keywords.
