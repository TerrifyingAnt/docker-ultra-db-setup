import csv, simplejson, decimal, codecs

data = open("Mobiles Dataset (2025).csv", encoding="UTF-8")
reader = csv.DictReader(data, delimiter=";", quotechar='"')

with codecs.open("out.json", "w", encoding="utf-8") as out:
   for r in reader:
      for k, v in r.items():
         # make sure nulls are generated
         if not v:
            r[k] = None
         # parse and generate decimal arrays
         elif k == "loc":
            r[k] = [decimal.Decimal(n) for n in v.strip("[]").split(",")]
         # generate a number
         elif k == "geonameid":
            r[k] = int(v)
      out.write(simplejson.dumps(r, ensure_ascii=False, use_decimal=True)+"\n")