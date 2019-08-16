**Сервер и клиент** для работы с логом, выполненный с помощью модуля **socket**.

Сервер:
---

Принимает от клиента строку в формате: **HH[:MM[:SS]]-<some_string>** и ищет по вхождению подстроки *<some_string>* в модуль (к примеру, "Kernel::System::AuthSession::DB::CheckSessionID"). Результаты фильтруются по указанному времени. 

**Данные** храняться в файле **"otrs_error.log"**. 

**Ответ** возвращается в виде **JSON-массива**, где элементы — строки лога.

#### Например:

> 12-Kernel::System::AuthSession::DB::CheckSessionID 

Вернуть все записи, где есть Kernel::System::AuthSession::DB::CheckSessionID в модуле с 12:00:00 по 12:59:59 за все даты

> 17:08-TicketSubjectClean 

Вернуть все записи, где в модуле присутствует подстрока TicketSubjectClean с 17:08:00 по 17:08:59 за все даты

> 23:12:56-Kernel 

Вернуть все записи за секунду 23:12:56 за все даты, где модуль содержит Kernel

Клиент:
---

Принимает на вход строку формата **HH[:MM[:SS]]-<some_string>** (к примеру, 23:54-DB::CheckSessionID), отправляет запрос на сервер и отображает ответ в следующем виде:

```
Найдено 6 совпадений:
[Sun Apr 2 23:54:15 2017][Error][Kernel::System::AuthSession::DB::CheckSessionID][49] Got no SessionID!!
[Sun Apr 2 23:54:18 2017][Error][Kernel::System::AuthSession::DB::CheckSessionID][49] Got no SessionID!!
[Sun Apr 2 23:54:24 2017][Error][Kernel::System::AuthSession::DB::CheckSessionID][49] Got no SessionID!!
[Sun Apr 2 23:54:46 2017][Error][Kernel::System::AuthSession::DB::CheckSessionID][49] Got no SessionID!!
[Sun Apr 2 23:54:49 2017][Error][Kernel::System::AuthSession::DB::CheckSessionID][49] Got no SessionID!!
[Sun Apr 2 23:54:54 2017][Error][Kernel::System::AuthSession::DB::CheckSessionID][49] Got no SessionID!!
```

Опциональное усложнение:

**Поиск** в логе осуществляется за **логарифмическое время** или быстрее за счёт пренебрежения затратами на ОЗУ (в разумных пределах).

Примечания:

Здесь используется *крайне ненадёжный, однако работающий* на тестовых запросах подход, при котором получение данных из сокета останавливается с помощью проверки **endwith()**. Я знаю про этот косяк, но пока никак его не исправлял, потому что проект игрушечный)
