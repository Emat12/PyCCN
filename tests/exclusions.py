from pyccn import Name, Interest, _pyccn

e = Interest.ExclusionFilter()
e.add_any()
e.add_names([Name.Name('/one'), Name.Name('/two'), Name.Name('/three'), Name.Name('/four')])
e.add_any()
e.add_name(Name.Name('/forty/two'))

str(e)
d = _pyccn.ExclusionFilter_obj_from_ccn(e.ccn_data)
str(d)

# I believe separation of /forty/two into /forty and /two is a correct behavior
# since it doesn't make sense to have more than one level in exclusions
result = ['<any>', '/one', '/two', '/four', '/three', '<any>', '/forty', '/two']

for a,b in zip(d.components, result):
	if str(a) == b:
		continue
	else:
		raise AssertionError("%s != %s" % (str(a), b))
