

def output_to_table(obj, oformat='latex', table_ends=False):
    """
    Compile the properties to a table.
    :param format:
    :return: para, str, table as a string
    """
    para = ""
    for item in obj.inputs:
        if hasattr(obj, item):
            if oformat == "latex":
                para += "{0} & {1}\\\\\n".format(item, getattr(obj, item))
    if table_ends:
        para = add_table_ends(para, oformat)
    return para


def add_table_ends(para, oformat='latex'):
    fpara = ""
    if oformat == 'latex':
        fpara += "\\begin{table}[cc]\n"
        fpara += "Parameter & Value \\\\\n"
        fpara += "\\hline \n"
        fpara += para
        fpara += "\\hline \n"
        fpara += "\\end{table}\n"
    return fpara
