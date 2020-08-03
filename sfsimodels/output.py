import numpy as np


def output_to_table(obj, olist='inputs', oformat='latex', table_ends=False, prefix=""):
    """
    Compile the properties to a table.

    Parameters
    ----------
    olist: list,
        Names of the parameters to be in the output table
    oformat: str,
        The type of table to be output
    table_ends: bool,
        Add ends to the table
    prefix: str,
        A string to be added to the start of each parameter name

    Returns
    -------
    para: str,
        Table as a string
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
            value = getattr(obj, item)
            try:
                value_str = format_value(value)
            except TypeError:
                value_str = ''
                pass
            if oformat == "latex":
                delimeter = " & "
            else:
                delimeter = ","
            para += "{0}{1}{2}\\\\\n".format(prefix + format_name(item), delimeter, value_str)
    if table_ends:
        para = add_table_ends(para, oformat)
    return para


def format_name(name):
    """
    Format parameter names for output

    Parameters
    ----------
    name: str
        Name to be formatted

    Returns
    -------
    str: Formatted name
    """
    name = name.replace("_", " ")
    return name


def format_value(value, sf=3):
    """
    Convert a parameter value into a formatted string with certain significant figures

    Parameters
    ----------
    value: float or list or array
        The value to be formatted
    sf: int
        The number of significant figures

    Returns
    -------
    str: formatted value
    """
    if isinstance(value, str):
        return value

    elif isinstance(value, list) or isinstance(value, np.ndarray):
        value = list(value)
        for i in range(len(value)):
            vv = format_value(value[i])
            value[i] = vv
        return "[" + ", ".join(value) + "]"

    elif value is None:
        return "N/A"

    else:
        fmt_str = "{0:.%ig}" % sf
        return fmt_str.format(value)


def add_table_ends(para, oformat='latex', caption="caption-text", label="table", np=2, align='c'):
    """
    Adds the latex table ends

    Parameters
    ----------
    para:
    oformat:
    caption:
    label:
    """
    if len(align) == 1:
        a_str = "".join([align] * np)
    else:
        a_str = align
    fpara = ""
    if oformat == 'latex':
        fpara += "\\begin{table}[H]\n"
        fpara += "\\centering\n"
        fpara += "\\begin{tabular}{%s}\n" % a_str
        fpara += "\\toprule\n"
        fpara += "Parameter & Value \\\\\n"
        fpara += "\\midrule\n"
        fpara += para
        fpara += "\\bottomrule\n"
        fpara += "\\end{tabular}\n"
        fpara += "\\caption{%s \label{tab:%s}}\n" % (caption, label)
        fpara += "\\end{table}\n\n"
    return fpara


# if __name__ == '__main__':
#     avalue = np.array([[0, 0]])
#     print(format_value(avalue))
