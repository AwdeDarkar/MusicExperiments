import time

import mingus.core.scales as scales
import mingus.core.chords as chords
from mingus.containers import Note, Track, Bar
from mingus.midi import fluidsynth

class Rhythm:
    def __init__(self):
        pass

    def __getitem__(self, index):
        raise NotImplementedError

    @classmethod
    def Even(cls, *meter):
        class EvenRhythm(Rhythm):
            def __getitem__(self, _):
                return meter[1]
        return EvenRhythm()

    @classmethod
    def Swung(cls, *meter):
        class SwungRhythm(Rhythm):
            def __getitem__(self, i):
                if i%2 == 0:
                    return meter[1] / 1.5
                return meter[1] * 2
        return SwungRhythm()

class Motion:
    def __init__(self, ante, cons, context, rhythm=Rhythm.Even(4,4), fill=[]):
        self.ante = ante
        self.cons = cons
        self.context = context
        self.rhythm = rhythm
        self.fill = fill

    def notes(self):
        notes = []
        notes.append((self.context[self.ante], self.rhythm[0]))
        i = 0
        for filler in self.fill:
            if isinstance(filler, Motion):
                notes += filler.notes()
            else:
                notes.append((self.context[filler], self.rhythm[i]))
            i += 1
        notes.append((self.context[self.cons], self.rhythm[i]))
        return notes

    def bars(self, meter=(4,4)):
        bars = [Bar(meter)]
        for note in self.notes():
            if not bars[-1].place_notes(*note):
                bars.append(Bar(meter))
                bars[-1].place_notes(*note)
        return bars

    def track(self, meter=(4,4)):
        bars = self.bars(meter)
        track = Track()
        for bar in bars:
            track.add_bar(bar)
        return track

    def play(self, player, bpm=100, meter=(4,4)):
        track = self.track(meter)
        beats = sum([bar.meter[0] for bar in track.bars])
        player.play_Track(track, 1, bpm)
        time.sleep(beats / (60 * bpm))

    def split(self, index):
        return (
                Motion(self.ante, self.fill[index], self.context, self.rhythm, self.fill[:index-1]),
                Motion(self.fill[index], self.cons, self.context, self.rhythm, self.fill[index:]),
                )

    def set_fill(self, fill):
        return Motion(self.ante, self.cons, self.context, self.rhythm, fill)

    def set_rhythm(self, rhythm):
        return Motion(self.ante, self.cons, self.context, rhythm, self.fill)

    def set_context(self, context):
        return Motion(self.ante, self.cons, context, self.rhythm, self.fill)

    def set_equivalent_context(self, context):
        cante = context.index(self.context[self.ante])
        ccons = context.index(self.context[self.cons])
        cfill = [context.index(self.context[i]) for i in self.fill]
        return Motion(cante, ccons, context, self.rhythm, cfill)

    def fill_interval(self):
        if self.ante < self.cons:
            return self.set_fill(list(range(self.ante+1, self.cons)))
        else:
            return self.set_fill(list(range(self.cons+1, self.ante))[::-1])

    def skip(self, skip):
        return self.set_fill([v for i, v in enumerate(self.fill) if i not in skip])


class MusicalContext:
    def __getitem__(self, index):
        """
        Get the indexed contextual note or chord; must support octave shifting for out-of-bounds
        """
        raise NotImplementedError

    def index(self, value):
        """ Calculate the index of the note or chord given; raise ValueError if it is not in context """
        raise NotImplementedError

    @property
    def parent(self):
        """ Return the 'parent' context, if any """
        return None

    @property
    def relatives(self):
        """
        Return any relative contexts (chord inversions, extensions, relative majors or minors,
        etc
        """
        return {}


class ScaleContext:
    def __init__(self, scale, octave=4):
        self.scale = scale
        self.octave = octave

    def __getitem__(self, index):
        return f"{self.scale.degree(index % 7 + 1)}-{self.octave + index//7}"

    def index(self, value):
        note, octave = value.split("-")
        return self.scale.ascending().index(note) + (7 * (self.octave - int(octave)))

class ChordContext:
    def __init__(self, chord, octave=4):
        self.chord = chord
        self.octave = octave

    def __getitem__(self, index):
        return f"{self.chord[(index % len(self.chord))]}-{self.octave + index//len(self.chord)}"

if __name__ == "__main__":
    fluidsynth.init("./soundfonts/piano/grand-piano.sf2", driver="alsa")
    m = Motion(7, 0, ChordContext(chords.triad("C", "D")))
    m\
            .fill_interval()\
            .play(fluidsynth)
