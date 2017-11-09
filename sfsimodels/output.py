

def output_to_table(obj, olist='inputs', oformat='latex', table_ends=False):
    """
    Compile the properties to a table.
    :param format:
    :return: para, str, table as a string
    """
    para = ""
    property_list = []
    if olist == 'inputs':
        property_list = obj.inputs
    elif olist == 'all':
        for item in obj.__dict__:
            if "_" != item[0]:
                property_list.append(item)
    for item in property_list:
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
