
class TrueClass:
    
    def __eq__(self, other):
        return type(self) == type(other)


class FalseClass:
    
    def __eq__(self, other):
        return type(self) == type(other)



def replace_bools_for_comparison(data):
    if isinstance(data, list):
        new_list = []
        for i in data:
            new_list.append(replace_bools_for_comparison(i))
        return new_list
    elif isinstance(data, dict):
        new_dict = {}
        for k,v in data.items():
            new_dict[k] = replace_bools_for_comparison(v)
        return new_dict
    elif data is True:
        return TrueClass()
    elif data is False:
        return FalseClass()
    else:
        return data
