from configparser import ConfigParser

def config(filename='database.ini', section='postgresql'):
    # create parser
    parser = ConfigParser()
    #read config file
    parser.read(filename)
    db = {}
    if parser.has_section(section):
        params = parser.items(section)
        for param in params:
            db[param[0]] = param[1]
    else:
        raise Exception(f'Section {section} is not found in the {filename} file')

    return db