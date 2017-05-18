
class Encoder(object):


    def __init__(self, vals, uniques):


    def ONEofN(self):


    def _arrays_index(self):


    def _internal_indexer(self):

        pass

# class Original(object):
#     def _simple_string_encoder(self, colname, strings):
#         enc_strings = []
#         if colname in [k for k in string_encoder_log.keys()]:
#             toint = string_encoder_log[colname][1]
#             for s in strings:
#                 sx = "".join(list(map(lambda x: str(toint[x]), list(s))))
#                 string_encoder_log[colname].append(int(sx))
#                 enc_strings.append(int(sx))
#
#         else:
#             stringslist = list(string.ascii_letters + string.punctuation)
#             toint = dict(map(lambda x: (stringslist[x], x+1), [i for i in range(len(stringslist))]))
#             fromint = dict(map(lambda x: (x+1, stringslist[x]), [i for i in range(len(stringslist))]))
#
#             for s in strings:
#                 sx = self.encoder_sep.join(list(map(lambda x: str(toint[x]), list(s))))
#                 enc_strings.append(int(sx))
#
#             string_encoder_log.update({colname: (fromint, toint, enc_strings, stringslist, self.encoder_sep)})
#
#         return enc_strings
#
#     def _simple_string_decoder(self, colname, strings):
#         txt_strings = []
#         if colname not in [k for k in string_encoder_log.keys()]:
#             raise KeyError("Invalid column! No Encoded Instance Found.")
#         else:
#             fromint, encoded_arrays = string_encoder_log[colname][0], [str(x) for x in string_encoder_log[colname][2]]
#             toint = string_encoder_log[colname][1]
#             encoder_sep = string_encoder_log[colname][4]
#             for encarr in encoded_arrays:
#                 txt = str(toint[encoder_sep]).join(list(map(lambda x: fromint[x], [int(i) for i in str(encarr).split(str(encoder_sep))])))
#                 txt_strings.append(txt)
#         return txt_strings
#
#     def _1ofN_name_encoder(self, col):
#         arrs = []
#
#         arrays = self.df[col]
#         v = self._compile_unique_value_set([array.split("|") for array in arrays])
#         if col in [k for k in array_encoder_log.keys()]:
#             uniques = array_encoder_log[col]["uniques"]
#             for arr in arrays:
#                 if any(arr) not in uniques:
#                     uniques.extend(arr)
#                     uni = array_encoder_log[col].update({"uniques": [u for u in np.unique(uniques)]})
#
#                     s=self._encoder_map(vals=arr, uniques=uni)
#                     arrs.append(s)
#                 else:
#                     s=self._encoder_map(vals=arr, uniques=uniques)
#                     arrs.append(s)
#         else:
#             array_encoder_log.update({col: {"uniques": v}})
#             for arr in arrays:
#                 s = self._encoder_map(vals=arr.split("|"), uniques=v)
#                 arrs.append(s)
#
#         return arrs
#
#     def _encoder_map(self, vals, uniques, sep="0000"):
#         print(vals)
#         dct = dict(map(lambda x: (uniques[x], str(x+1)), [i for i in range(len(uniques))]))
#         return sep.join([dct[v] for v in vals])
#
#     def _decoder_map(self, val, uniques, sep="0000"):
#         dct = dict(map(lambda x: (str(x+1), uniques[x]), [y for y in range(len(uniques))]))
#         return [dct[i] for i in val.split(sep)]
#
#     def _1ofN_name_decoder(self, colname, arrays):
#         arrs=[]
#         if colname not in [k for k in array_encoder_log.keys()]:
#             raise KeyError("Invalid column! No Encoded Instance Found.")
#         else:
#             encoder_IDs, encoded_arrays = array_encoder_log[colname][0], [str(x) for x in array_encoder_log[colname][2]]
#             encoder_sep = array_encoder_log[colname][4]
#             for encarr in encoded_arrays:
#                 txtarr = list(map(lambda x: encoder_IDs[x], encarr.split(encoder_sep)))
#                 arrs.append(txtarr)
#         return arrs
#
#     def _compile_unique_value_set(self, arrays):
#         lst = []
#         for array in arrays:
#             lst.extend(array)
#
#         return [x for x in np.unique(lst)]
#
#     def encode_columns(self, cols):
#         encoder="array"
#
#         if self.user_encoder is None:
#             if encoder == "array":
#                 for col in cols:
#                     self.df[col] = [int(c) for c in self._1ofN_name_encoder(col)]
#         else:
#             try:
#                 self.df.apply(lambda x: self.user_encoder(x))
#             except Exception as err:
#                 print("Error: Check user encoder. \n %s" % err)
#

