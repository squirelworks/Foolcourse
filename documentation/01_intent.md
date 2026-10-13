# Intent

Foolcourse is a course platform. A person opens it, sees a catalog,
picks a course, and the course opens in Foolbook. Progress and scores
are kept. That is the product.

ATT is one use of it, not the product. The Navy electronics curriculum
that started this work is the first official list. A school, a company,
or a person can point Foolcourse at a different folder and a different
list and get the same platform. Nothing in the path has to say ATT.

## What a deployment is

A deployment is three things:

- a courses folder
- an official list
- a student file

Anything in the folder that is not on the official list is extra
material. Extra material is catalogued, can be opened, and keeps its
own score. It does not count toward the overall score.

This is the rule that makes the platform usable for more than one
purpose. ATT marks ATT Master as official and leaves the rating tracks
as extra. A later deployment marks its own list and leaves its own
supplements as extra. The rule does not change.

## What it is not

- Not a remake of the Nida ATT shell. The shell is one source of courses.
- Not a ToolBook runtime. Foolbook reads books. The 8.1 engine is a
  separate question, recorded in [07_toolbook.md](07_toolbook.md).
- Not a school administration system. Foolversity makes the files.
  Foolcourse reads them. Neither enrolls, bills, or grades a cohort.
