

Reader Libraries
=================

This is an index 3,000 scholarly journal articles on the topic of digital libraries.

Through the use of this tool the active reader (you) will enhance their use and understanding of the corpus. The whole thing kinda, sorta works like a back-of-the-book index but on steroids.


Requirements
------------

Reader Libraries ought to run on any computer with Python version 3.12 or greater installed. 


Installation
------------

First, Reader Libraries is a Python application. Open your terminal and run the following command, and version number greater than or equal to 3.12 ought to work:

    python --version

Second, Reader Libraries requires the installation of [Ollama](https://ollama.com), a tool making it easy to run generative-AI applications on your local computer. Visit https://ollama.com/download and install Ollama. It is not hard. I promise.

Third, Reader Libraries is configured to use two specific large language mnodels. Open your terminal and install Deepseek:

    ollama pull deepseek-v3.1:671b-cloud

Then install nomic-embed-text:

    ollama pull nomic-embed-text:latest

Fourth, as if this writing, Reader Libraries can only be downloaded from GitHub. Open your terminal and run the following command which will download the Reader Lite software. Mind you, since the application includes a number of indexes, the download is not small, but it is not too big either:

    git clone https://github.com/ericleasemorgan/reader-libraries.git

Fifth, install the software, and begin by changing directories to where the software was downloaded:

    cd reader-libraries

Use pip to do the actual installation, and power-users may want to install the tool in a virtual environment:

    pip install .

If you got this far, then the hard parts are over.

Sixth, launch Reader Libraries with the following command:

    flask --app reader_libraries run --debug

Finally, open http://127.0.0.1:5000 in your Web browser, and you ought to see something very similar to the following:

<img width="1322" height="917" alt="reader-libraries" src="https://github.com/user-attachments/assets/5208efd3-db48-4ea8-b189-5793edda139c" />

Congratuations, you have successfully installed and launched Reader Libraries. Whew.

Next time, just run the following command to pick up where you left off:

    flask --app reader_libraries run --debug

While I can write rubust Python applications, I am still rusty on the writing of Python installation tools. Any help with the above instructions would be greatly appreciated!

---
Eric Lease Morgan &lt;eric_morgan@infomotions.com&gt;  
October 24, 2025
