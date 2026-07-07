from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# MySQL bağlantı adresimiz (Şifre 123456 olarak ayarlandı)
SQLALCHEMY_DATABASE_URL = "mysql+pymysql://root:123456@localhost:3306/tarim_kds"

# Veritabanı motorunu (Engine) ayağa kaldırıyoruz
engine = create_engine(SQLALCHEMY_DATABASE_URL)

# Veritabanı ile her işlem yaptığımızda açılıp kapanacak olan oturum (Session) yöneticisi
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Python'daki sınıflarımızı (Class) MySQL'deki tablolara dönüştürecek olan ana yapı
Base = declarative_base()