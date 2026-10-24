from .models import Discipline, Professeur


def discipline_pour(nom):
    nom = ' '.join((nom or '').split())
    d = Discipline.objects.filter(nom__iexact=nom).first()
    return d or Discipline.objects.create(nom=nom[:1].upper() + nom[1:])


def prochain_code_prof():
    last = Professeur.objects.exclude(code__isnull=True).order_by('-code').first()
    n = int(last.code.split('-')[1]) + 1 if last else 1
    return f'PRF-{n:04d}'
