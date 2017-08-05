var ops = [];

db.property_list_rental.aggregate([
  { "$group": {
    "_id": "$property_id",
    "ids": { "$push": "$_id" },
    "count": { "$sum": 1 }
  }},
  { "$match": { "count": { "$gt": 1 } } }
]).forEach( doc => {

  var keep = doc.ids.shift();

  ops = [
    ...ops,
    {
      "deleteMany": { "filter": { "_id": { "$in": doc.ids }, "property_area" : { "$exists" : false } } }
    }
  ];

  if (ops.length >= 500) {
    db.property_list_rental.bulkWrite(ops);
    ops = [];
  }
});

db.property_list_rental.bulkWrite(ops);
ops = [];

db.property_list_rental.aggregate([
  { "$group": {
    "_id": "$property_id",
    "ids": { "$push": "$_id" },
    "count": { "$sum": 1 }
  }},
  { "$match": { "count": { "$gt": 1 } } }
]).forEach( doc => {
  ops = [
    ...ops,
    {
      "deleteMany": { "filter": { "_id": { "$in": doc.ids }, "property_area" : { "$exists" : false }, "property_size_unit" : { "$exists" : false }, "property_price_unit" : { "$exists" : false }  } }
    }
  ];

  if (ops.length >= 500) {
    db.property_list_rental.bulkWrite(ops);
    ops = [];
  }
});

db.property_list_rental.bulkWrite(ops);
ops = [];

db.property_list_rental.aggregate([
  { "$group": {
    "_id": "$property_id",
    "ids": { "$push": "$_id" },
    "count": { "$sum": 1 }
  }},
  { "$match": { "count": { "$gt": 1 } } }
]).forEach( doc => {

  var keep = doc.ids.shift();

  ops = [
    ...ops,
    {
      "deleteMany": { "filter": { "_id": { "$in": doc.ids } } }
    }
  ];

  if (ops.length >= 500) {
    db.property_list_rental.bulkWrite(ops);
    ops = [];
  }
});

db.property_list_rental.bulkWrite(ops);


db.property_list_rental.find().forEach(function(obj){
   db.property_list.insert(obj)
})

db.property_list.updateMany(
   { "type": "rent" },
   { $set:
      {
        "type": "lease"
      }
   }
)

db.property_list.updateMany(
   {"vendor": , "last_crawled_date": {"$gt": ISODate("2017-07-30")}},
   { $set:
      {
        "last_crawled_date": null
      }
   }
)

db.property_list.aggregate(
[
  { "$group": {
    "_id": "$property_id",
    "ids": { "$push": "$link" },
    "count": { "$sum": 1 }
  }},
  { $match: {
    count: { $gte: 2 }
  } },
  { $sort : { count : -1} },
  { $limit : 10 }
],
{ allowDiskUse: true}
);

db.property_list.aggregate(
[ { $match: { "last_crawled_date": {"$gt": ISODate("2017-07-20")} } },
  { "$group": {
    "_id": "$property_id",
    "created_dates": { "$push": "$created_date" },
    "links": { "$push": "$link" },
    "count": { "$sum": 1 }
  }},
  { $match: {
    count: { $gte: 2 }
  } },
  { $sort : { count : -1} },
  { $limit : 10 }
],
{ allowDiskUse: true}
);