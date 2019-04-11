from autopwn2.database import db


class Setting(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String, nullable=False)
    value = db.Column(db.String, nullable=False)
    example = db.Column(db.String, nullable=True)

    def __init__(self, name, value, example):
        self.name = name
        self.value = value
        self.example = example

    def __str__(self):
        return "<{} '{}: {} //{}'>".format(self.__class__.__name__, self.name, self.value, self.example)


class Tool(db.Model):
    """ Tool Model for storing tool related details """
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    description = db.Column(db.String, nullable=True)
    command = db.Column(db.String, nullable=False)
    name = db.Column(db.String, nullable=False)
    url = db.Column(db.String, nullable=True)
    stdout = db.Column(db.Integer, nullable=False)

    def __init__(self, name, command, description, url, stdout):
        self.name = name
        self.command = command
        self.description = description
        self.url = url
        self.stdout = stdout

    def __str__(self):
        return "<{} '{} //{}'>".format(self.__class__.__name__, self.name, self.description)


class Job(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    command = db.Column(db.String, nullable=False)
    startTime = db.Column(db.DateTime, nullable=True)
    endTime = db.Column(db.DateTime, nullable=True)
    return_code = db.Column(db.Integer, default=-1)

    tool_id = db.Column(db.Integer, db.ForeignKey('tool.id'))
    tool = db.relationship('Tool', backref=db.backref('jobs', lazy='dynamic'))

    def __init__(self, command, tool):
        self.command = command
        self.tool = tool

    def __str__(self):
        return "<{} '{} //{}'>".format(self.__class__.__name__, self.tool.name, self.command)


assessment_tools = db.Table('assessment_tools',
                            db.Column('assessment_id', db.Integer, db.ForeignKey('assessment.id', ondelete="CASCADE")),
                            db.Column('tool_id', db.Integer, db.ForeignKey('tool.id'))
                            )


class Assessment(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String, nullable=False)
    description = db.Column(db.String, nullable=True)
    tools = db.relationship('Tool', secondary='assessment_tools', cascade='all, delete',
                            backref=db.backref('assessments', lazy='joined', single_parent=True), lazy='dynamic',
                            )

    def __init__(self, name, description):
        self.name = name
        self.description = description

    def __str__(self):
        return "<{} '{} //{}'>".format(self.__class__.__name__, self.name, self.description)
