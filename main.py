from src.extracao import extracao

if __name__ == '__main__':
    extracao.serve(
        name="extracao-diaria",
        cron="0 20 * * *" # todos os dias às 20:00
         
    )