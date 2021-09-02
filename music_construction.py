import time

import mingus.core.scales as scales
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

    def play(self, player, bpm=90, meter=(4,4)):
        track = self.track(meter)
        beats = sum([bar.meter[0] for bar in track.bars])
        player.play_Track(track, 1, bpm)
        time.sleep(bpm * beats / 60)

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
        cante = self.context[self.ante]
        ccons = self.context[self.cons]
        return Motion(context.index(cante), context.index(ccons), context, self.rhythm, self.fill)

    def fill_interval(self):
        return self.set_fill(list(range(self.ante+1, self.cons+1)))

class ScaleContext:
    def __init__(self, scale):
        self.scale = scale

    def __getitem__(self, index):
        return self.scale.degree(index)

if __name__ == "__main__":
    fluidsynth.init("./soundfonts/piano/grand-piano.sf2", driver="alsa")
    m = Motion(1, 7, ScaleContext(scales.Ionian("C")))
    m.fill_interval().play(fluidsynth)

