import warnings

from nbformat import read as _read, reads as _reads
from nbformat import write as _write, writes as _writes
from .common import BaseValidator, ValidationError

class ValidatorV1(BaseValidator):

    schema = None

    def __init__(self):
        super(ValidatorV1, self).__init__(1)

    def _upgrade_v0_to_v1(self, cell):
        meta = cell.metadata['nbgrader']

        if 'grade' not in meta:
            meta['grade'] = False
        if 'solution' not in meta:
            meta['solution'] = False
        if 'locked' not in meta:
            meta['locked'] = False

        if not meta['grade'] and not meta['solution'] and not meta['locked']:
            if 'grade_id' in meta:
                del meta['grade_id']
            if 'points' in meta:
                del meta['points']

        if 'points' in meta:
            if meta['points'] == '':
                meta['points'] = 0.0
            else:
                meta['points'] = float(meta['points'])

        allowed = set(self.schema["properties"].keys())
        keys = set(meta.keys()) - allowed
        if len(keys) > 0:
            warnings.warn("extra keys detected in metadata, these will be removed: {}".format(keys))
            for key in keys:
                del meta[key]

        meta['schema_version'] = 1

        return cell

    def upgrade_cell_metadata(self, cell):
        if 'nbgrader' not in cell.metadata:
            return cell

        meta = cell.metadata['nbgrader']

        if 'schema_version' not in meta:
            warnings.warn("nbgrader schema version is not defined, assuming version 0")
            meta['schema_version'] = 0

        if meta['schema_version'] == 0:
            cell = self._upgrade_v0_to_v1(cell)

        return cell

    def validate_cell(self, cell):
        super(ValidatorV1, self).validate_cell(self.upgrade_cell_metadata(cell))

        if 'nbgrader' not in cell.metadata:
            return

        meta = cell.metadata['nbgrader']
        grade = meta['grade']
        solution = meta['solution']
        locked = meta['locked']

        # check for a valid grade id
        if grade or solution or locked:
            if 'grade_id' not in meta:
                raise ValidationError("nbgrader cell does not have a grade_id: {}".format(cell.source))
            if meta['grade_id'] == '':
                raise ValidationError("grade_id is empty")

        # check for valid points
        if grade:
            if 'points' not in meta:
                raise ValidationError("nbgrader cell '{}' does not have points".format(
                    meta['grade_id']))

        # check that markdown cells are grade AND solution (not either/or)
        if cell.cell_type == "markdown" and grade and not solution:
            raise ValidationError(
                "Markdown grade cell '{}' is not marked as a solution cell".format(
                    meta['grade_id']))
        if cell.cell_type == "markdown" and not grade and solution:
            raise ValidationError(
                "Markdown solution cell is not marked as a grade cell: {}".format(cell.source))

    def validate_nb(self, nb):
        super(ValidatorV1, self).validate_nb(nb)

        ids = set([])
        for cell in nb.cells:

            if 'nbgrader' not in cell.metadata:
                continue

            grade = cell.metadata['nbgrader']['grade']
            solution = cell.metadata['nbgrader']['solution']
            locked = cell.metadata['nbgrader']['locked']

            if not grade and not solution and not locked:
                continue

            grade_id = cell.metadata['nbgrader']['grade_id']
            if grade_id in ids:
                raise ValidationError("Duplicate grade id: {}".format(grade_id))
            ids.add(grade_id)


def read_v1(source, **kwargs):
    nb = _read(source, **kwargs)
    ValidatorV1().validate_nb(nb)
    return nb


def write_v1(nb, **kwargs):
    ValidatorV1().validate_nb(nb)
    return _write(nb, **kwargs)


def reads_v1(source, **kwargs):
    nb = _reads(source, **kwargs)
    ValidatorV1().validate_nb(nb)
    return nb


def writes_v1(nb, **kwargs):
    ValidatorV1().validate_nb(nb)
    return _writes(nb, **kwargs)
